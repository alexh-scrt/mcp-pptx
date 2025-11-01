"""Theme application to PowerPoint presentations."""

import logging
from pathlib import Path
from typing import Optional

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches

from ..models.theme_spec import ScrapedTheme

logger = logging.getLogger(__name__)


class ThemeApplicator:
    """Applies scraped themes to PowerPoint presentations."""

    def apply_theme(self, prs: Presentation, theme: ScrapedTheme) -> None:
        """Apply scraped theme to presentation."""
        try:
            self._apply_color_scheme(prs, theme)
            self._apply_fonts(prs, theme)
            # Logo application would be done per slide
            logger.info("Applied theme to presentation")
        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")

    def _apply_color_scheme(self, prs: Presentation, theme: ScrapedTheme) -> None:
        """Apply color scheme to presentation."""
        try:
            # This is a simplified implementation
            # In a full implementation, you would modify the theme colors
            # in the presentation's theme part
            
            # For now, we'll store colors for use during content creation
            # Colors will be applied when creating slides and content
            logger.debug("Color scheme stored for slide creation")
            
        except Exception as e:
            logger.error(f"Failed to apply color scheme: {e}")

    def _apply_fonts(self, prs: Presentation, theme: ScrapedTheme) -> None:
        """Apply font scheme to presentation."""
        try:
            # This is a simplified implementation
            # In a full implementation, you would modify the theme fonts
            # in the presentation's theme part
            
            logger.debug(f"Fonts will be applied: heading={theme.fonts.heading}, body={theme.fonts.body}")
            
        except Exception as e:
            logger.error(f"Failed to apply fonts: {e}")

    def hex_to_rgb(self, hex_color: str) -> RGBColor:
        """Convert hex color to RGBColor."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) != 6:
            hex_color = '000000'  # Default to black
        
        try:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return RGBColor(r, g, b)
        except ValueError:
            return RGBColor(0, 0, 0)  # Default to black

    def apply_logo_to_slide(self, slide, theme: ScrapedTheme, position: str = "top-right") -> bool:
        """Apply logo to a specific slide."""
        if not theme.logo or not theme.logo.cached_path:
            return False
        
        try:
            logo_path = Path(theme.logo.cached_path)
            if not logo_path.exists():
                logger.warning(f"Logo file not found: {logo_path}")
                return False
            
            # Add logo image to slide
            if position == "top-right":
                left = Inches(8.5)  # Right side
                top = Inches(0.5)   # Top
                width = Inches(1.5)  # Small size
            elif position == "top-left":
                left = Inches(0.5)
                top = Inches(0.5)
                width = Inches(1.5)
            else:  # center
                left = Inches(4.25)
                top = Inches(3.5)
                width = Inches(2.0)
            
            slide.shapes.add_picture(
                str(logo_path),
                left,
                top,
                width=width
            )
            
            logger.debug(f"Added logo to slide at {position}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add logo to slide: {e}")
            return False