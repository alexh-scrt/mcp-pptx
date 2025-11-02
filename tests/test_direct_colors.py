#!/usr/bin/env python3
"""Test script to verify direct color/font specification."""

import asyncio
import json
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer


async def test_direct_colors():
    """Test that direct colors and fonts can be specified."""

    # Create a deck spec with direct colors and fonts
    deck_spec_data = {
        "title": "Test Direct Colors",
        "subtitle": "Custom theme without scraping",
        "theme": {
            "colors": {
                "primary": "#E3342F",    # Red
                "secondary": "#FFE9D3",   # Light Peach
                "accent": "#1CCBD0",      # Cyan
                "background": "#FFFFFF",  # White
                "text": "#111827"         # Dark Gray
            },
            "fonts": {
                "heading": "Calibri",
                "body": "Tahoma"
            }
        },
        "slides": [
            {
                "layout": "TITLE",
                "title": "Direct Color Test",
                "subtitle": "Using directly specified colors"
            },
            {
                "layout": "TITLE_CONTENT",
                "title": "Content Slide",
                "content": [
                    "This uses the direct color specification",
                    "Primary color (Red): #E3342F",
                    "Accent color (Cyan): #1CCBD0"
                ]
            }
        ],
        "output": {
            "filename": "test_direct_colors.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("Creating deck specification with direct colors...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)

    print(f"Theme scraped: {deck_spec.theme.scraped}")
    if deck_spec.theme.scraped:
        print(f"  Colors - Primary: {deck_spec.theme.scraped.colors.primary}")
        print(f"  Fonts - Heading: {deck_spec.theme.scraped.fonts.heading}")
        print(f"  Source: {deck_spec.theme.scraped.source_url}")

    print("\nGenerating presentation...")
    renderer = PresentationRenderer()
    result = await renderer.generate_presentation(deck_spec)

    print(f"\nResult: {json.dumps(result, indent=2)}")

    if result.get("ok"):
        print(f"\n✅ SUCCESS! Presentation saved to: {result['output']}")
        print(f"   Slides generated: {result['slides_generated']}")
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_direct_colors())
    exit(0 if success else 1)
