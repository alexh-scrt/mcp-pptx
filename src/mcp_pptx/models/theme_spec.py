"""Theme specification models."""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ColorPalette(BaseModel):
    """Color palette extracted from a website."""
    
    primary: str = Field(..., description="Primary brand color (hex)")
    secondary: str = Field(..., description="Secondary color (hex)")
    accent: str = Field(..., description="Accent color (hex)")
    background: str = Field(..., description="Background color (hex)")
    text: str = Field(..., description="Text color (hex)")


class FontPalette(BaseModel):
    """Font palette for presentations."""
    
    heading: str = Field(..., description="PowerPoint-safe heading font")
    body: str = Field(..., description="PowerPoint-safe body font")
    heading_web: Optional[str] = Field(None, description="Original web heading font")
    body_web: Optional[str] = Field(None, description="Original web body font")


class LogoSpec(BaseModel):
    """Logo specification."""
    
    url: HttpUrl = Field(..., description="Original URL of the logo")
    cached_path: Optional[str] = Field(None, description="Local cached file path")
    width: Optional[int] = Field(None, description="Logo width in pixels")
    height: Optional[int] = Field(None, description="Logo height in pixels")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")


class ScrapedTheme(BaseModel):
    """Result from scraping a website's theme."""
    
    colors: ColorPalette = Field(..., description="Color palette")
    fonts: FontPalette = Field(..., description="Font palette")
    logo: Optional[LogoSpec] = Field(None, description="Logo specification")
    source_url: HttpUrl = Field(..., description="Source URL that was scraped")
    warnings: List[str] = Field(default_factory=list, description="Extraction warnings")


class ThemeSpec(BaseModel):
    """Theme specification for presentations."""
    
    scraped: Optional[ScrapedTheme] = Field(None, description="Scraped theme data")
    template: Optional[str] = Field(None, description="Path to PowerPoint template file")
    
    def model_post_init(self, __context) -> None:
        """Validate that at least one theme source is provided."""
        if not self.scraped and not self.template:
            raise ValueError("Either scraped theme or template must be provided")