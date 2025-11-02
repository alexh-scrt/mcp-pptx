#!/usr/bin/env python3
"""Test script to verify default theme application."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer


async def test_default_theme():
    """Test that default theme is applied when theme is empty."""

    # Create a simple deck spec with empty theme
    deck_spec_data = {
        "title": "Test Default Theme",
        "subtitle": "Verifying Secret AI default colors",
        "theme": {},  # Empty theme - should use default
        "slides": [
            {
                "layout": "TITLE",
                "title": "Test Presentation",
                "subtitle": "Using Default Secret AI Theme"
            },
            {
                "layout": "TITLE_CONTENT",
                "title": "Content Slide",
                "content": [
                    "This should have a white background",
                    "With a red title bar at the top",
                    "And black text"
                ]
            },
            {
                "layout": "SECTION",
                "title": "Section Divider"
            }
        ],
        "output": {
            "filename": "test_default_theme.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("Creating deck specification...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)

    print(f"Theme scraped: {deck_spec.theme.scraped}")
    print(f"Theme template: {deck_spec.theme.template}")
    print(f"Theme colors: {deck_spec.theme.colors}")
    print(f"Theme fonts: {deck_spec.theme.fonts}")

    print("\nInitializing renderer...")
    renderer = PresentationRenderer()

    print(f"Default theme loaded: {renderer._default_theme is not None}")
    if renderer._default_theme:
        print(f"  Primary color: {renderer._default_theme.colors.primary}")
        print(f"  Secondary color: {renderer._default_theme.colors.secondary}")
        print(f"  Accent color: {renderer._default_theme.colors.accent}")
        print(f"  Background color: {renderer._default_theme.colors.background}")
        print(f"  Text color: {renderer._default_theme.colors.text}")
        print(f"  Heading font: {renderer._default_theme.fonts.heading}")
        print(f"  Body font: {renderer._default_theme.fonts.body}")

    print("\nGenerating presentation...")
    result = await renderer.generate_presentation(deck_spec)

    print(f"\nResult: {json.dumps(result, indent=2)}")

    if result.get("ok"):
        print(f"\n✅ SUCCESS! Presentation saved to: {result['output']}")
        print(f"   Slides generated: {result['slides_generated']}")
        if result.get('warnings'):
            print(f"   Warnings: {result['warnings']}")
    else:
        print(f"\n❌ FAILED: {result.get('error')}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_default_theme())
    exit(0 if success else 1)
