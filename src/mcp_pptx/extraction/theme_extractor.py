"""Web theme extraction using Playwright."""

import asyncio
import hashlib
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

from playwright.async_api import Browser, Page, async_playwright
from PIL import Image
import httpx

from ..models.theme_spec import ColorPalette, FontPalette, LogoSpec, ScrapedTheme
from ..cache.asset_cache import AssetCache

logger = logging.getLogger(__name__)


class ThemeExtractor:
    """Extracts themes from websites using Playwright."""

    # Font mapping from web fonts to PowerPoint-safe fonts
    FONT_MAPPINGS = {
        "Montserrat": "Calibri Light",
        "Roboto": "Calibri",
        "Open Sans": "Arial",
        "Lato": "Calibri",
        "Poppins": "Gill Sans MT",
        "Inter": "Calibri",
        "Source Sans Pro": "Arial",
        "Nunito": "Calibri",
        "Raleway": "Calibri Light",
        "Ubuntu": "Arial",
        "Merriweather": "Georgia",
        "Playfair Display": "Times New Roman",
        "Oswald": "Arial Black",
        "PT Sans": "Arial",
        "Libre Baskerville": "Georgia",
    }

    def __init__(self) -> None:
        self.asset_cache = AssetCache()

    async def extract_theme(
        self,
        url: str,
        extract_logo: bool = True,
        selector_hints: Optional[Dict[str, str]] = None
    ) -> ScrapedTheme:
        """Extract theme from a website."""
        warnings: List[str] = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Extract colors
                colors = await self._extract_colors(page)
                
                # Extract fonts
                fonts = await self._extract_fonts(page)
                
                # Extract logo if requested
                logo = None
                if extract_logo:
                    try:
                        logo = await self._extract_logo(page, url, selector_hints)
                    except Exception as e:
                        logger.warning(f"Logo extraction failed: {e}")
                        warnings.append(f"Could not extract logo: {str(e)}")
                
                return ScrapedTheme(
                    colors=colors,
                    fonts=fonts,
                    logo=logo,
                    source_url=url,
                    warnings=warnings
                )
                
            finally:
                await browser.close()

    async def _extract_colors(self, page: Page) -> ColorPalette:
        """Extract color palette from page."""
        # Try CSS custom properties first
        css_vars = await page.evaluate("""
            () => {
                const styles = getComputedStyle(document.documentElement);
                const vars = {};
                
                // Common CSS variable names
                const colorVars = [
                    '--primary-color', '--brand-color', '--main-color',
                    '--secondary-color', '--accent-color',
                    '--background-color', '--bg-color',
                    '--text-color', '--foreground-color'
                ];
                
                colorVars.forEach(varName => {
                    const value = styles.getPropertyValue(varName).trim();
                    if (value) {
                        vars[varName] = value;
                    }
                });
                
                return vars;
            }
        """)
        
        # Extract colors from common elements
        element_colors = await page.evaluate("""
            () => {
                const colors = {};
                
                // Header/navigation
                const header = document.querySelector('header, nav, .header, .navbar');
                if (header) {
                    const headerStyles = getComputedStyle(header);
                    colors.header_bg = headerStyles.backgroundColor;
                    colors.header_color = headerStyles.color;
                }
                
                // Body
                const body = document.body;
                const bodyStyles = getComputedStyle(body);
                colors.body_bg = bodyStyles.backgroundColor;
                colors.body_color = bodyStyles.color;
                
                // Primary headings
                const h1 = document.querySelector('h1');
                if (h1) {
                    colors.h1_color = getComputedStyle(h1).color;
                }
                
                // Links
                const link = document.querySelector('a');
                if (link) {
                    colors.link_color = getComputedStyle(link).color;
                }
                
                return colors;
            }
        """)
        
        # Parse and normalize colors
        primary = self._parse_color(
            css_vars.get('--primary-color') or 
            css_vars.get('--brand-color') or 
            css_vars.get('--main-color') or
            element_colors.get('header_bg') or
            element_colors.get('link_color') or
            '#005596'
        )
        
        secondary = self._parse_color(
            css_vars.get('--secondary-color') or
            self._derive_secondary_color(primary)
        )
        
        accent = self._parse_color(
            css_vars.get('--accent-color') or
            self._derive_accent_color(primary)
        )
        
        background = self._parse_color(
            css_vars.get('--background-color') or
            css_vars.get('--bg-color') or
            element_colors.get('body_bg') or
            '#FFFFFF'
        )
        
        text = self._parse_color(
            css_vars.get('--text-color') or
            css_vars.get('--foreground-color') or
            element_colors.get('body_color') or
            element_colors.get('h1_color') or
            '#333333'
        )
        
        return ColorPalette(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text=text
        )

    async def _extract_fonts(self, page: Page) -> FontPalette:
        """Extract font palette from page."""
        fonts = await page.evaluate("""
            () => {
                const fonts = {};
                
                // Get computed font families
                const h1 = document.querySelector('h1, h2, .title, .heading');
                if (h1) {
                    fonts.heading = getComputedStyle(h1).fontFamily;
                }
                
                const body = document.body;
                fonts.body = getComputedStyle(body).fontFamily;
                
                const p = document.querySelector('p, .content, .text');
                if (p) {
                    fonts.bodyText = getComputedStyle(p).fontFamily;
                }
                
                return fonts;
            }
        """)
        
        # Extract and clean font names
        heading_font = self._extract_font_name(fonts.get('heading') or fonts.get('body', ''))
        body_font = self._extract_font_name(fonts.get('bodyText') or fonts.get('body', ''))
        
        # Map to PowerPoint-safe fonts
        heading_pptx = self.FONT_MAPPINGS.get(heading_font, 'Calibri')
        body_pptx = self.FONT_MAPPINGS.get(body_font, 'Arial')
        
        return FontPalette(
            heading=heading_pptx,
            body=body_pptx,
            heading_web=heading_font if heading_font != heading_pptx else None,
            body_web=body_font if body_font != body_pptx else None
        )

    async def _extract_logo(
        self, 
        page: Page, 
        base_url: str,
        selector_hints: Optional[Dict[str, str]] = None
    ) -> Optional[LogoSpec]:
        """Extract logo from page."""
        # Common logo selectors
        selectors = [
            'header img[alt*="logo" i]',
            'nav img[alt*="logo" i]',
            '.logo img',
            '.brand img',
            '.navbar-brand img',
            'header img:first-child',
            'nav img:first-child',
            '.header img:first-child'
        ]
        
        # Add custom selector hints
        if selector_hints and 'logo' in selector_hints:
            selectors.insert(0, selector_hints['logo'])
        
        for selector in selectors:
            try:
                logo_element = await page.query_selector(selector)
                if logo_element:
                    # Get logo attributes
                    src = await logo_element.get_attribute('src')
                    alt = await logo_element.get_attribute('alt')
                    
                    if src:
                        # Convert relative URL to absolute
                        logo_url = urljoin(base_url, src)
                        
                        # Get dimensions
                        bbox = await logo_element.bounding_box()
                        width = int(bbox['width']) if bbox else None
                        height = int(bbox['height']) if bbox else None
                        
                        # Download and cache logo
                        cached_path = await self.asset_cache.download_image(logo_url)
                        
                        return LogoSpec(
                            url=logo_url,
                            cached_path=str(cached_path) if cached_path else None,
                            width=width,
                            height=height,
                            alt_text=alt
                        )
            except Exception as e:
                logger.debug(f"Failed to extract logo with selector {selector}: {e}")
                continue
        
        return None

    def _parse_color(self, color_str: str) -> str:
        """Parse color string and convert to hex."""
        if not color_str or color_str == 'transparent':
            return '#000000'
        
        color_str = color_str.strip()
        
        # Already hex
        if color_str.startswith('#'):
            return color_str.upper()
        
        # RGB/RGBA
        rgb_match = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)', color_str)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return f'#{r:02X}{g:02X}{b:02X}'
        
        # Named colors (basic support)
        named_colors = {
            'black': '#000000',
            'white': '#FFFFFF',
            'red': '#FF0000',
            'green': '#008000',
            'blue': '#0000FF',
            'navy': '#000080',
            'gray': '#808080',
            'grey': '#808080',
        }
        
        return named_colors.get(color_str.lower(), '#000000')

    def _derive_secondary_color(self, primary: str) -> str:
        """Derive secondary color from primary."""
        # Simple approach: lighten the primary color
        try:
            # Convert hex to RGB
            hex_color = primary.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Lighten by 30%
            factor = 1.3
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            return f'#{r:02X}{g:02X}{b:02X}'
        except:
            return '#0A77C0'  # Default fallback

    def _derive_accent_color(self, primary: str) -> str:
        """Derive accent color from primary."""
        # Simple approach: shift hue
        try:
            # For simplicity, return a complementary color
            hex_color = primary.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
            # Complementary color (rough approximation)
            r = 255 - r
            g = 255 - g
            b = 255 - b
            
            return f'#{r:02X}{g:02X}{b:02X}'
        except:
            return '#FF5733'  # Default fallback

    def _extract_font_name(self, font_family: str) -> str:
        """Extract clean font name from CSS font-family."""
        if not font_family:
            return 'Arial'
        
        # Split by comma and take first font
        fonts = [f.strip().strip('"\'') for f in font_family.split(',')]
        
        # Filter out generic families
        generic_families = {'serif', 'sans-serif', 'monospace', 'cursive', 'fantasy'}
        
        for font in fonts:
            if font.lower() not in generic_families:
                return font
        
        return 'Arial'

    def merge_themes(self, themes: List[ScrapedTheme], priority: str = "balanced") -> ScrapedTheme:
        """Merge multiple themes into one."""
        if not themes:
            raise ValueError("No themes provided")
        
        if len(themes) == 1:
            return themes[0]
        
        if priority == "first":
            base_theme = themes[0]
            # Use first theme's colors and fonts, but merge warnings
            warnings = []
            for theme in themes:
                warnings.extend(theme.warnings)
            
            return ScrapedTheme(
                colors=base_theme.colors,
                fonts=base_theme.fonts,
                logo=base_theme.logo,
                source_url=base_theme.source_url,
                warnings=warnings
            )
        
        # Balanced approach - use most common colors/fonts
        # For simplicity, use first theme but could implement voting
        base_theme = themes[0]
        all_warnings = []
        for theme in themes:
            all_warnings.extend(theme.warnings)
        
        return ScrapedTheme(
            colors=base_theme.colors,
            fonts=base_theme.fonts,
            logo=base_theme.logo,
            source_url=f"merged:{','.join(t.source_url for t in themes)}",
            warnings=all_warnings
        )