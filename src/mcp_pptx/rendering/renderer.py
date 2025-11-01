"""Main PowerPoint presentation renderer."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from pptx import Presentation
from pptx.util import Inches

from ..models.deck_spec import DeckSpec, LayoutType
from ..models.theme_spec import ScrapedTheme
from .layouts import LayoutManager
from .theme_applicator import ThemeApplicator
from .content_fillers import ContentFiller

logger = logging.getLogger(__name__)


class PresentationRenderer:
    """Renders PowerPoint presentations from DeckSpec."""

    def __init__(self) -> None:
        self.layout_manager = LayoutManager()
        self.theme_applicator = ThemeApplicator()
        self.content_filler = ContentFiller()

    async def list_templates(self) -> List[Dict[str, Any]]:
        """List available PowerPoint templates."""
        templates_dir = Path("themes")
        templates = []
        
        # Create default template info
        default_template = {
            "name": "default",
            "path": "themes/default.potx",
            "layouts": [layout.value for layout in LayoutType],
            "description": "Built-in default template"
        }
        templates.append(default_template)
        
        # Scan for additional templates
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.potx"):
                if template_file.name != "default.potx":
                    template_info = {
                        "name": template_file.stem,
                        "path": str(template_file),
                        "layouts": [layout.value for layout in LayoutType],  # Assume all layouts available
                        "description": f"Custom template: {template_file.stem}"
                    }
                    templates.append(template_info)
        
        return templates

    async def generate_presentation(self, deck_spec: DeckSpec) -> Dict[str, Any]:
        """Generate PowerPoint presentation from deck specification."""
        warnings = []
        assets_downloaded = []
        
        try:
            # Create presentation
            if deck_spec.theme.template and Path(deck_spec.theme.template).exists():
                prs = Presentation(deck_spec.theme.template)
                logger.info(f"Using template: {deck_spec.theme.template}")
            else:
                prs = Presentation()
                logger.info("Using default presentation template")
                if deck_spec.theme.template:
                    warnings.append(f"Template {deck_spec.theme.template} not found, using default")
            
            # Apply theme if scraped theme is available
            if deck_spec.theme.scraped:
                self.theme_applicator.apply_theme(prs, deck_spec.theme.scraped)
                logger.info("Applied scraped theme to presentation")
            
            # Generate slides
            slides_generated = 0
            for slide_spec in deck_spec.slides:
                try:
                    # Get appropriate layout
                    layout = self.layout_manager.get_layout(prs, slide_spec.layout)
                    if not layout:
                        layout = self.layout_manager.get_layout(prs, LayoutType.TITLE_CONTENT)
                        warnings.append(f"Layout {slide_spec.layout} not found, using TITLE_CONTENT")
                    
                    # Add slide
                    slide = prs.slides.add_slide(layout)
                    
                    # Fill content
                    slide_warnings = await self.content_filler.fill_slide(
                        slide, slide_spec, deck_spec.theme.scraped
                    )
                    warnings.extend(slide_warnings)
                    
                    slides_generated += 1
                    logger.debug(f"Generated slide {slides_generated}: {slide_spec.title}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate slide {slides_generated + 1}: {e}")
                    warnings.append(f"Failed to generate slide {slides_generated + 1}: {str(e)}")
            
            # Apply footer if specified
            if deck_spec.footer:
                self._apply_footer(prs, deck_spec.footer)
            
            # Generate output filename
            output_file = self._generate_output_path(deck_spec)
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save presentation
            prs.save(str(output_file))
            logger.info(f"Saved presentation to: {output_file}")
            
            return {
                "ok": True,
                "output": str(output_file),
                "slides_generated": slides_generated,
                "warnings": warnings,
                "assets_downloaded": assets_downloaded
            }
            
        except Exception as e:
            logger.exception("Failed to generate presentation")
            return {
                "ok": False,
                "error": str(e),
                "output": None,
                "slides_generated": 0,
                "warnings": warnings,
                "assets_downloaded": assets_downloaded
            }

    def _generate_output_path(self, deck_spec: DeckSpec) -> Path:
        """Generate output file path."""
        output_dir = Path(deck_spec.output.directory)
        
        if deck_spec.output.filename:
            filename = deck_spec.output.filename
        else:
            # Generate filename from title and timestamp
            safe_title = "".join(c for c in deck_spec.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title.replace(' ', '_').lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.{deck_spec.output.format}"
        
        return output_dir / filename

    def _apply_footer(self, prs: Presentation, footer_spec) -> None:
        """Apply footer to all slides."""
        # This is a simplified implementation
        # In a real implementation, you'd need to handle footer placeholders
        # and different slide masters
        logger.debug("Footer application not fully implemented yet")
        pass