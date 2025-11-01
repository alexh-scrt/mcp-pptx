"""Test data models."""

import pytest
from pydantic import ValidationError

from mcp_pptx.models.deck_spec import DeckSpec, SlideSpec, LayoutType, ContentType, SlideContent
from mcp_pptx.models.theme_spec import ScrapedTheme, ColorPalette, FontPalette, ThemeSpec


def test_color_palette_creation():
    """Test ColorPalette model creation."""
    colors = ColorPalette(
        primary="#005596",
        secondary="#0A77C0",
        accent="#FF5733",
        background="#FFFFFF",
        text="#333333"
    )
    
    assert colors.primary == "#005596"
    assert colors.secondary == "#0A77C0"
    assert colors.accent == "#FF5733"
    assert colors.background == "#FFFFFF"
    assert colors.text == "#333333"


def test_font_palette_creation():
    """Test FontPalette model creation."""
    fonts = FontPalette(
        heading="Calibri Light",
        body="Arial",
        heading_web="Montserrat",
        body_web="Open Sans"
    )
    
    assert fonts.heading == "Calibri Light"
    assert fonts.body == "Arial"
    assert fonts.heading_web == "Montserrat"
    assert fonts.body_web == "Open Sans"


def test_scraped_theme_creation():
    """Test ScrapedTheme model creation."""
    colors = ColorPalette(
        primary="#005596",
        secondary="#0A77C0", 
        accent="#FF5733",
        background="#FFFFFF",
        text="#333333"
    )
    
    fonts = FontPalette(
        heading="Calibri Light",
        body="Arial"
    )
    
    theme = ScrapedTheme(
        colors=colors,
        fonts=fonts,
        source_url="https://example.com",
        warnings=["Test warning"]
    )
    
    assert theme.colors.primary == "#005596"
    assert theme.fonts.heading == "Calibri Light"
    assert theme.source_url == "https://example.com"
    assert len(theme.warnings) == 1


def test_slide_content_creation():
    """Test SlideContent model creation."""
    content = SlideContent(
        type=ContentType.TEXT,
        text="This is test content"
    )
    
    assert content.type == ContentType.TEXT
    assert content.text == "This is test content"
    
    bullet_content = SlideContent(
        type=ContentType.BULLETS,
        bullets=["Point 1", "Point 2", "Point 3"]
    )
    
    assert bullet_content.type == ContentType.BULLETS
    assert len(bullet_content.bullets) == 3


def test_slide_spec_creation():
    """Test SlideSpec model creation."""
    slide = SlideSpec(
        title="Test Slide",
        subtitle="Test Subtitle",
        layout=LayoutType.TITLE_CONTENT,
        content=[
            SlideContent(
                type=ContentType.TEXT,
                text="Test content"
            )
        ],
        speaker_notes="Test notes"
    )
    
    assert slide.title == "Test Slide"
    assert slide.layout == LayoutType.TITLE_CONTENT
    assert len(slide.content) == 1


def test_deck_spec_creation():
    """Test DeckSpec model creation."""
    theme = ThemeSpec(
        template="themes/default.potx"
    )
    
    slide = SlideSpec(
        title="Test Slide",
        layout=LayoutType.TITLE_CONTENT
    )
    
    deck = DeckSpec(
        title="Test Presentation",
        theme=theme,
        slides=[slide]
    )
    
    assert deck.title == "Test Presentation"
    assert len(deck.slides) == 1
    assert deck.theme.template == "themes/default.potx"


def test_theme_spec_validation():
    """Test ThemeSpec validation."""
    # Should fail with neither scraped nor template
    with pytest.raises(ValidationError):
        ThemeSpec()
    
    # Should pass with template only
    theme1 = ThemeSpec(template="themes/default.potx")
    assert theme1.template == "themes/default.potx"
    
    # Should pass with scraped only
    colors = ColorPalette(
        primary="#005596",
        secondary="#0A77C0",
        accent="#FF5733", 
        background="#FFFFFF",
        text="#333333"
    )
    fonts = FontPalette(heading="Calibri", body="Arial")
    scraped = ScrapedTheme(
        colors=colors,
        fonts=fonts,
        source_url="https://example.com"
    )
    
    theme2 = ThemeSpec(scraped=scraped)
    assert theme2.scraped is not None


if __name__ == "__main__":
    pytest.main([__file__])