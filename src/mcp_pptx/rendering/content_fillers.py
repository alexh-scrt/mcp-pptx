"""Content filling for PowerPoint slides."""

import logging
from pathlib import Path
from typing import List, Optional

from pptx.slide import Slide
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from ..models.deck_spec import SlideSpec, ContentType
from ..models.theme_spec import ScrapedTheme
from .theme_applicator import ThemeApplicator

logger = logging.getLogger(__name__)


class ContentFiller:
    """Fills slide content based on specifications."""

    def __init__(self) -> None:
        self.theme_applicator = ThemeApplicator()

    async def fill_slide(
        self,
        slide: Slide,
        slide_spec: SlideSpec,
        theme: Optional[ScrapedTheme] = None
    ) -> List[str]:
        """Fill slide with content based on specification."""
        warnings = []
        
        try:
            # Fill title and subtitle
            if slide_spec.title:
                success = self._fill_title(slide, slide_spec.title, theme)
                if not success:
                    warnings.append(f"Could not set title: {slide_spec.title}")
            
            if slide_spec.subtitle:
                success = self._fill_subtitle(slide, slide_spec.subtitle, theme)
                if not success:
                    warnings.append(f"Could not set subtitle: {slide_spec.subtitle}")
            
            # Fill content
            for content in slide_spec.content:
                content_warnings = await self._fill_content(slide, content, theme)
                warnings.extend(content_warnings)
            
            # Add speaker notes
            if slide_spec.speaker_notes:
                self._add_speaker_notes(slide, slide_spec.speaker_notes)
            
            # Add logo if available
            if theme and theme.logo:
                success = self.theme_applicator.apply_logo_to_slide(slide, theme, "top-right")
                if not success:
                    warnings.append("Could not add logo to slide")
            
        except Exception as e:
            logger.error(f"Failed to fill slide: {e}")
            warnings.append(f"Error filling slide: {str(e)}")
        
        return warnings

    def _fill_title(self, slide: Slide, title: str, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill slide title."""
        try:
            # Find title placeholder
            title_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and 'title' in shape.name.lower():
                    title_placeholder = shape
                    break
            
            if not title_placeholder:
                # Try placeholder index 0 (usually title)
                if len(slide.placeholders) > 0:
                    title_placeholder = slide.placeholders[0]
            
            if title_placeholder and hasattr(title_placeholder, 'text'):
                title_placeholder.text = title
                
                # Apply theme colors if available
                if theme:
                    try:
                        text_frame = title_placeholder.text_frame
                        paragraph = text_frame.paragraphs[0]
                        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
                        
                        # Set font
                        run.font.name = theme.fonts.heading
                        run.font.size = Pt(32)  # Large title font
                        
                        # Set color
                        primary_color = self.theme_applicator.hex_to_rgb(theme.colors.primary)
                        run.font.color.rgb = primary_color
                        
                    except Exception as e:
                        logger.debug(f"Could not apply theme to title: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill title: {e}")
        
        return False

    def _fill_subtitle(self, slide: Slide, subtitle: str, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill slide subtitle."""
        try:
            # Find subtitle placeholder
            subtitle_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and 'subtitle' in shape.name.lower():
                    subtitle_placeholder = shape
                    break
            
            if not subtitle_placeholder and len(slide.placeholders) > 1:
                # Try placeholder index 1 (usually subtitle)
                subtitle_placeholder = slide.placeholders[1]
            
            if subtitle_placeholder and hasattr(subtitle_placeholder, 'text'):
                subtitle_placeholder.text = subtitle
                
                # Apply theme if available
                if theme:
                    try:
                        text_frame = subtitle_placeholder.text_frame
                        paragraph = text_frame.paragraphs[0]
                        run = paragraph.runs[0] if paragraph.runs else paragraph.add_run()
                        
                        run.font.name = theme.fonts.body
                        run.font.size = Pt(18)
                        
                        text_color = self.theme_applicator.hex_to_rgb(theme.colors.text)
                        run.font.color.rgb = text_color
                        
                    except Exception as e:
                        logger.debug(f"Could not apply theme to subtitle: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill subtitle: {e}")
        
        return False

    async def _fill_content(
        self,
        slide: Slide,
        content,
        theme: Optional[ScrapedTheme] = None
    ) -> List[str]:
        """Fill slide content based on content type."""
        warnings = []
        
        try:
            if content.type == ContentType.TEXT:
                success = self._fill_text(slide, content.text or "", theme)
                if not success:
                    warnings.append("Could not add text content")
                    
            elif content.type == ContentType.BULLETS:
                success = self._fill_bullets(slide, content.bullets or [], theme)
                if not success:
                    warnings.append("Could not add bullet points")
                    
            elif content.type == ContentType.IMAGE:
                if content.image:
                    success = await self._fill_image(slide, content.image, theme)
                    if not success:
                        warnings.append(f"Could not add image: {content.image.url}")
                        
            elif content.type == ContentType.TABLE:
                if content.table:
                    success = self._fill_table(slide, content.table, theme)
                    if not success:
                        warnings.append("Could not add table")
                        
            elif content.type == ContentType.CHART:
                if content.chart:
                    success = self._fill_chart(slide, content.chart, theme)
                    if not success:
                        warnings.append("Could not add chart")
                        
        except Exception as e:
            logger.error(f"Failed to fill content: {e}")
            warnings.append(f"Error filling content: {str(e)}")
        
        return warnings

    def _fill_text(self, slide: Slide, text: str, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill text content."""
        try:
            # Find content placeholder
            content_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and ('content' in shape.name.lower() or 'body' in shape.name.lower()):
                    content_placeholder = shape
                    break
            
            if content_placeholder and hasattr(content_placeholder, 'text'):
                content_placeholder.text = text
                
                # Apply theme
                if theme:
                    try:
                        text_frame = content_placeholder.text_frame
                        for paragraph in text_frame.paragraphs:
                            for run in paragraph.runs:
                                run.font.name = theme.fonts.body
                                run.font.size = Pt(14)
                                text_color = self.theme_applicator.hex_to_rgb(theme.colors.text)
                                run.font.color.rgb = text_color
                    except Exception as e:
                        logger.debug(f"Could not apply theme to text: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill text: {e}")
        
        return False

    def _fill_bullets(self, slide: Slide, bullets: List[str], theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill bullet points."""
        try:
            # Find content placeholder
            content_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and ('content' in shape.name.lower() or 'body' in shape.name.lower()):
                    content_placeholder = shape
                    break
            
            if content_placeholder and hasattr(content_placeholder, 'text_frame'):
                text_frame = content_placeholder.text_frame
                text_frame.clear()  # Clear existing content
                
                for i, bullet in enumerate(bullets):
                    if i == 0:
                        p = text_frame.paragraphs[0]
                    else:
                        p = text_frame.add_paragraph()
                    
                    p.text = bullet
                    p.level = 0  # Top level bullet
                    
                    # Apply theme
                    if theme:
                        try:
                            for run in p.runs:
                                run.font.name = theme.fonts.body
                                run.font.size = Pt(14)
                                text_color = self.theme_applicator.hex_to_rgb(theme.colors.text)
                                run.font.color.rgb = text_color
                        except Exception as e:
                            logger.debug(f"Could not apply theme to bullets: {e}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill bullets: {e}")
        
        return False

    async def _fill_image(self, slide: Slide, image_spec, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill image content."""
        try:
            # For now, add placeholder text indicating where image would go
            # In a full implementation, you would download and insert the actual image
            
            # Find content placeholder
            content_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and ('content' in shape.name.lower() or 'body' in shape.name.lower()):
                    content_placeholder = shape
                    break
            
            if content_placeholder and hasattr(content_placeholder, 'text'):
                placeholder_text = f"[IMAGE: {image_spec.url}]"
                if image_spec.alt_text:
                    placeholder_text += f"\nAlt text: {image_spec.alt_text}"
                if image_spec.caption:
                    placeholder_text += f"\nCaption: {image_spec.caption}"
                
                content_placeholder.text = placeholder_text
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill image: {e}")
        
        return False

    def _fill_table(self, slide: Slide, table_spec, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill table content."""
        try:
            # For now, add placeholder text
            # In a full implementation, you would create an actual table
            
            content_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and ('content' in shape.name.lower() or 'body' in shape.name.lower()):
                    content_placeholder = shape
                    break
            
            if content_placeholder and hasattr(content_placeholder, 'text'):
                table_text = f"[TABLE]\nHeaders: {', '.join(table_spec.headers)}\n"
                table_text += f"Rows: {len(table_spec.rows)} rows of data"
                
                content_placeholder.text = table_text
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill table: {e}")
        
        return False

    def _fill_chart(self, slide: Slide, chart_spec, theme: Optional[ScrapedTheme] = None) -> bool:
        """Fill chart content."""
        try:
            # For now, add placeholder text
            # In a full implementation, you would create an actual chart
            
            content_placeholder = None
            for shape in slide.placeholders:
                if hasattr(shape, 'text') and ('content' in shape.name.lower() or 'body' in shape.name.lower()):
                    content_placeholder = shape
                    break
            
            if content_placeholder and hasattr(content_placeholder, 'text'):
                chart_text = f"[CHART: {chart_spec.type}]"
                if chart_spec.title:
                    chart_text += f"\nTitle: {chart_spec.title}"
                
                content_placeholder.text = chart_text
                return True
                
        except Exception as e:
            logger.error(f"Failed to fill chart: {e}")
        
        return False

    def _add_speaker_notes(self, slide: Slide, notes: str) -> None:
        """Add speaker notes to slide."""
        try:
            if hasattr(slide, 'notes_slide') and hasattr(slide.notes_slide, 'notes_text_frame'):
                slide.notes_slide.notes_text_frame.text = notes
                logger.debug("Added speaker notes to slide")
        except Exception as e:
            logger.error(f"Failed to add speaker notes: {e}")