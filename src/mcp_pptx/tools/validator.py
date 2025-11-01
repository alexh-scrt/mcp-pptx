"""Deck specification validator."""

import logging
from pathlib import Path
from typing import List
import httpx

from ..models.deck_spec import DeckSpec, ValidationResult, ContentType, LayoutType

logger = logging.getLogger(__name__)


class DeckValidator:
    """Validates deck specifications before generation."""

    async def validate_deck(self, deck_spec: DeckSpec) -> ValidationResult:
        """Validate deck specification."""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Validate basic structure
            if not deck_spec.title.strip():
                errors.append("Deck title cannot be empty")
            
            if not deck_spec.slides:
                errors.append("Deck must contain at least one slide")
            
            # Validate theme
            theme_valid = await self._validate_theme(deck_spec.theme, warnings)
            if not theme_valid:
                errors.append("Invalid theme specification")
            
            # Validate each slide
            for i, slide in enumerate(deck_spec.slides, 1):
                slide_warnings, slide_suggestions = await self._validate_slide(slide, i)
                warnings.extend(slide_warnings)
                suggestions.extend(slide_suggestions)
            
            # Validate output specification
            self._validate_output(deck_spec.output, warnings)
            
            # Check for potential improvements
            self._suggest_improvements(deck_spec, suggestions)
            
            # Determine if deck is valid (no errors)
            valid = len(errors) == 0
            
            return ValidationResult(
                valid=valid,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            logger.exception("Error during deck validation")
            return ValidationResult(
                valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=warnings,
                suggestions=suggestions
            )

    async def _validate_theme(self, theme, warnings: List[str]) -> bool:
        """Validate theme specification."""
        try:
            # Check if template exists (if specified)
            if theme.template:
                template_path = Path(theme.template)
                if not template_path.exists():
                    warnings.append(f"Template file not found: {theme.template}")
                elif not template_path.suffix.lower() in ['.potx', '.pptx']:
                    warnings.append(f"Template file should be .potx or .pptx: {theme.template}")
            
            # Check scraped theme
            if theme.scraped:
                # Validate colors
                if not self._is_valid_hex_color(theme.scraped.colors.primary):
                    warnings.append("Invalid primary color format")
                
                # Check if logo is accessible
                if theme.scraped.logo:
                    if theme.scraped.logo.cached_path:
                        logo_path = Path(theme.scraped.logo.cached_path)
                        if not logo_path.exists():
                            warnings.append(f"Cached logo file not found: {theme.scraped.logo.cached_path}")
                    else:
                        # Try to check URL accessibility
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.head(str(theme.scraped.logo.url))
                                if response.status_code >= 400:
                                    warnings.append(f"Logo URL not accessible: {theme.scraped.logo.url}")
                        except Exception:
                            warnings.append(f"Could not verify logo URL: {theme.scraped.logo.url}")
            
            # Must have either template or scraped theme
            if not theme.template and not theme.scraped:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Theme validation failed: {e}")
            return False

    async def _validate_slide(self, slide, slide_number: int) -> tuple[List[str], List[str]]:
        """Validate individual slide."""
        warnings = []
        suggestions = []
        
        try:
            # Check for content appropriateness
            content_count = len(slide.content)
            
            if content_count == 0 and not slide.title:
                warnings.append(f"Slide {slide_number}: Slide appears to be empty")
            
            if content_count > 5:
                suggestions.append(f"Slide {slide_number}: Consider splitting content across multiple slides (has {content_count} content elements)")
            
            # Validate content elements
            for j, content in enumerate(slide.content):
                await self._validate_content(content, slide_number, j + 1, warnings, suggestions)
            
            # Layout suggestions
            if slide.layout == LayoutType.TWO_COL and content_count != 2:
                suggestions.append(f"Slide {slide_number}: TWO_COL layout works best with exactly 2 content elements")
            
            if slide.layout == LayoutType.IMAGE_FOCUS:
                has_image = any(c.type == ContentType.IMAGE for c in slide.content)
                if not has_image:
                    suggestions.append(f"Slide {slide_number}: IMAGE_FOCUS layout should contain an image")
            
        except Exception as e:
            warnings.append(f"Slide {slide_number}: Error during validation: {str(e)}")
        
        return warnings, suggestions

    async def _validate_content(self, content, slide_num: int, content_num: int, warnings: List[str], suggestions: List[str]) -> None:
        """Validate content element."""
        try:
            prefix = f"Slide {slide_num}, content {content_num}:"
            
            if content.type == ContentType.TEXT:
                if not content.text or not content.text.strip():
                    warnings.append(f"{prefix} Text content is empty")
                elif len(content.text) > 500:
                    suggestions.append(f"{prefix} Text is quite long, consider breaking into bullet points")
            
            elif content.type == ContentType.BULLETS:
                if not content.bullets:
                    warnings.append(f"{prefix} Bullet list is empty")
                elif len(content.bullets) > 7:
                    suggestions.append(f"{prefix} Too many bullets ({len(content.bullets)}), consider splitting")
                else:
                    for bullet in content.bullets:
                        if len(bullet) > 100:
                            suggestions.append(f"{prefix} Bullet point is quite long")
            
            elif content.type == ContentType.IMAGE:
                if not content.image:
                    warnings.append(f"{prefix} Image content missing image specification")
                else:
                    # Check URL format
                    url = content.image.url
                    if not url.startswith(('http://', 'https://', '/')):
                        warnings.append(f"{prefix} Invalid image URL format: {url}")
                    
                    # Try to check if image is accessible
                    if url.startswith('http'):
                        try:
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.head(url)
                                if response.status_code >= 400:
                                    warnings.append(f"{prefix} Image URL not accessible: {url}")
                        except Exception:
                            warnings.append(f"{prefix} Could not verify image URL: {url}")
            
            elif content.type == ContentType.TABLE:
                if not content.table:
                    warnings.append(f"{prefix} Table content missing table specification")
                else:
                    if not content.table.headers:
                        warnings.append(f"{prefix} Table missing headers")
                    if not content.table.rows:
                        warnings.append(f"{prefix} Table has no data rows")
                    elif len(content.table.rows) > 10:
                        suggestions.append(f"{prefix} Table has many rows ({len(content.table.rows)}), consider pagination")
            
            elif content.type == ContentType.CHART:
                if not content.chart:
                    warnings.append(f"{prefix} Chart content missing chart specification")
                else:
                    if not content.chart.data:
                        warnings.append(f"{prefix} Chart missing data")
                    if content.chart.type not in ['bar', 'line', 'pie', 'column', 'area']:
                        warnings.append(f"{prefix} Unsupported chart type: {content.chart.type}")
        
        except Exception as e:
            warnings.append(f"Slide {slide_num}, content {content_num}: Validation error: {str(e)}")

    def _validate_output(self, output, warnings: List[str]) -> None:
        """Validate output specification."""
        try:
            # Check output directory
            output_dir = Path(output.directory)
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                except Exception:
                    warnings.append(f"Cannot create output directory: {output.directory}")
            
            # Check filename if specified
            if output.filename:
                if not output.filename.endswith(f'.{output.format}'):
                    warnings.append(f"Output filename should end with .{output.format}")
                
                # Check for invalid characters
                invalid_chars = '<>:"/\\|?*'
                if any(char in output.filename for char in invalid_chars):
                    warnings.append("Output filename contains invalid characters")
        
        except Exception as e:
            warnings.append(f"Output validation error: {str(e)}")

    def _suggest_improvements(self, deck_spec: DeckSpec, suggestions: List[str]) -> None:
        """Suggest general improvements."""
        try:
            # Check slide count
            slide_count = len(deck_spec.slides)
            if slide_count > 20:
                suggestions.append(f"Presentation is quite long ({slide_count} slides), consider breaking into sections")
            
            # Check for variety in layouts
            layouts_used = set(slide.layout for slide in deck_spec.slides)
            if len(layouts_used) == 1 and slide_count > 5:
                suggestions.append("Consider using different layouts for visual variety")
            
            # Check for title slide
            has_title_slide = any(slide.layout == LayoutType.TITLE for slide in deck_spec.slides)
            if not has_title_slide:
                suggestions.append("Consider adding a title slide at the beginning")
            
            # Check for section breaks
            if slide_count > 10:
                has_section_slides = any(slide.layout == LayoutType.SECTION for slide in deck_spec.slides)
                if not has_section_slides:
                    suggestions.append("Consider adding section slides to break up long presentations")
        
        except Exception as e:
            logger.debug(f"Error generating suggestions: {e}")

    def _is_valid_hex_color(self, color: str) -> bool:
        """Check if string is valid hex color."""
        if not color or not color.startswith('#'):
            return False
        
        hex_part = color[1:]
        if len(hex_part) not in [3, 6]:
            return False
        
        try:
            int(hex_part, 16)
            return True
        except ValueError:
            return False