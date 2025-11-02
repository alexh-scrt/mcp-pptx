#!/usr/bin/env python3
"""Comprehensive test of all layout types with default theme."""

import asyncio
import json
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer


async def test_all_layouts():
    """Test all layout types with default theme."""

    deck_spec_data = {
        "title": "Comprehensive Layout Test",
        "subtitle": "Testing all layouts with Secret AI default theme",
        "theme": {},  # Use default theme
        "slides": [
            # TITLE slide (Red background)
            {
                "layout": "TITLE",
                "title": "Welcome to the Test",
                "subtitle": "All Layouts with Default Theme"
            },
            # TITLE_CONTENT slide (White background with red title bar)
            {
                "layout": "TITLE_CONTENT",
                "title": "Title with Content",
                "content": [
                    "First bullet point",
                    "Second bullet point with more text",
                    "Third bullet point"
                ]
            },
            # SECTION slide #1 (Cyan background)
            {
                "layout": "SECTION",
                "title": "Section 1"
            },
            # TITLE_CONTENT
            {
                "layout": "TITLE_CONTENT",
                "title": "Content Slide in Section 1",
                "content": [
                    "This slide is part of section 1",
                    "It should have white background",
                    "With red title bar"
                ]
            },
            # SECTION slide #2 (Red background)
            {
                "layout": "SECTION",
                "title": "Section 2"
            },
            # TWO_COL layout
            {
                "layout": "TWO_COL",
                "title": "Two Column Layout",
                "content": {
                    "left": [
                        "Left column item 1",
                        "Left column item 2",
                        "Left column item 3"
                    ],
                    "right": [
                        "Right column item 1",
                        "Right column item 2",
                        "Right column item 3"
                    ]
                }
            },
            # SECTION slide #3 (Light Peach background)
            {
                "layout": "SECTION",
                "title": "Section 3"
            },
            # IMAGE_FOCUS (if available)
            {
                "layout": "TITLE_CONTENT",
                "title": "Image Focus Placeholder",
                "content": [
                    "This would be an image-focused slide",
                    "Currently using TITLE_CONTENT as fallback"
                ]
            },
            # BLANK slide
            {
                "layout": "BLANK"
            },
            # Final slide
            {
                "layout": "TITLE",
                "title": "Thank You!",
                "subtitle": "Test Complete"
            }
        ],
        "output": {
            "filename": "test_all_layouts.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("=" * 60)
    print("COMPREHENSIVE LAYOUT TEST WITH DEFAULT THEME")
    print("=" * 60)

    print("\nCreating deck specification...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)
    print(f"  Title: {deck_spec.title}")
    print(f"  Slides: {len(deck_spec.slides)}")
    print(f"  Theme: {'Default (empty)' if not deck_spec.theme.scraped else 'Custom'}")

    print("\nInitializing renderer...")
    renderer = PresentationRenderer()

    if renderer._default_theme:
        print("  ✅ Default theme loaded successfully")
        print(f"     - Primary (Red): {renderer._default_theme.colors.primary}")
        print(f"     - Secondary (Peach): {renderer._default_theme.colors.secondary}")
        print(f"     - Accent (Cyan): {renderer._default_theme.colors.accent}")
        print(f"     - Background: {renderer._default_theme.colors.background}")
        print(f"     - Text: {renderer._default_theme.colors.text}")
    else:
        print("  ❌ Default theme NOT loaded")

    print("\nGenerating presentation...")
    result = await renderer.generate_presentation(deck_spec)

    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)

    if result.get("ok"):
        print(f"✅ SUCCESS!")
        print(f"   Output: {result['output']}")
        print(f"   Slides: {result['slides_generated']}")
        if result.get('warnings'):
            print(f"   Warnings: {len(result['warnings'])}")
            for warning in result['warnings']:
                print(f"     - {warning}")
        else:
            print(f"   Warnings: None")

        # Verify file exists
        output_path = Path(result['output'])
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"   File size: {file_size:.1f} KB")
            print(f"\n✅ ALL TESTS PASSED!")
        else:
            print(f"\n❌ ERROR: Output file not found at {output_path}")
            return False
    else:
        print(f"❌ FAILED: {result.get('error')}")
        if result.get('warnings'):
            print("Warnings:")
            for warning in result['warnings']:
                print(f"  - {warning}")
        return False

    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_all_layouts())
    exit(0 if success else 1)
