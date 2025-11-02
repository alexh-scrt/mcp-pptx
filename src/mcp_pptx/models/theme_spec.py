"""Theme specification models."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, HttpUrl, field_validator


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

    url: Optional[Union[HttpUrl, str]] = Field(None, description="Original URL of the logo")
    cached_path: Optional[str] = Field(None, description="Local cached file path")
    width: Optional[int] = Field(None, description="Logo width in pixels")
    height: Optional[int] = Field(None, description="Logo height in pixels")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")

    @field_validator('url', mode='before')
    @classmethod
    def normalize_url(cls, v: Any) -> Optional[str]:
        """Normalize URL field - allow None or convert to string."""
        if v is None:
            return None
        return str(v)

    @classmethod
    def model_validate(cls, obj: Any, **kwargs):
        """Custom validation to handle 'path' field and ignore extra fields."""
        if isinstance(obj, dict):
            # Create a copy to avoid modifying the original
            obj = dict(obj)

            # Handle 'path' field - map it to cached_path if url is not present
            if 'path' in obj and 'cached_path' not in obj:
                obj['cached_path'] = obj.pop('path')
                # If no URL provided, use a dummy file:// URL
                if 'url' not in obj or obj.get('url') is None:
                    obj['url'] = f"file://{obj['cached_path']}"

            # Remove 'position' if present (it's used in theme, not logo spec)
            obj.pop('position', None)

        return super().model_validate(obj, **kwargs)


class ScrapedTheme(BaseModel):
    """Result from scraping a website's theme."""

    colors: ColorPalette = Field(..., description="Color palette")
    fonts: FontPalette = Field(..., description="Font palette")
    logo: Optional[LogoSpec] = Field(None, description="Logo specification")
    source_url: str = Field("unknown", description="Source URL that was scraped (defaults to 'unknown' if not provided)")
    warnings: List[str] = Field(default_factory=list, description="Extraction warnings")


class ThemeSpec(BaseModel):
    """Theme specification for presentations."""

    scraped: Optional[ScrapedTheme] = Field(None, description="Scraped theme data")
    template: Optional[str] = Field(None, description="Path to PowerPoint template file")
    colors: Optional[ColorPalette] = Field(None, description="Direct color palette (alternative to scraped)")
    fonts: Optional[FontPalette] = Field(None, description="Direct font palette (alternative to scraped)")
    logo: Optional[LogoSpec] = Field(None, description="Direct logo specification (alternative to scraped)")

    def model_post_init(self, __context) -> None:
        """Validate that at least one theme source is provided."""
        # If colors and fonts are provided directly, create a scraped theme
        if self.colors and self.fonts and not self.scraped:
            self.scraped = ScrapedTheme(
                colors=self.colors,
                fonts=self.fonts,
                logo=self.logo,  # Include logo if provided
                source_url="direct",
                warnings=["Theme provided directly without web scraping"]
            )

        # Note: Validation relaxed - if no theme provided, renderer will use default theme
        # Only validate if theme specification is incomplete (e.g., colors but no fonts)
        if (self.colors and not self.fonts) or (self.fonts and not self.colors):
            raise ValueError("If providing colors or fonts directly, both must be provided")