#!/usr/bin/env python3
"""Test script to verify bullet splitting rules (colon and dash)."""

import asyncio
import json
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer


async def test_bullet_splitting():
    """Test both colon and dash bullet splitting rules."""

    deck_spec_data = {
        "title": "Bullet Formatting Test",
        "subtitle": "Testing bold formatting with colon and dash rules",
        "theme": {},  # Use default theme
        "slides": [
            # Title slide
            {
                "layout": "TITLE",
                "title": "Bullet Formatting Test",
                "subtitle": "Colon and Dash Rules"
            },
            # Test colon rule (1 word)
            {
                "layout": "TITLE_CONTENT",
                "title": "Colon Rule - Single Word",
                "content": [
                    "Goal: This should have 'Goal:' in bold",
                    "Note: Only the first part should be bold",
                    "Warning: Everything before colon is bold"
                ]
            },
            # Test colon rule (2-4 words)
            {
                "layout": "TITLE_CONTENT",
                "title": "Colon Rule - Multiple Words",
                "content": [
                    "Key Point: This should work with 2 words",
                    "Important Note: This has 2 words before colon",
                    "Critical Success Factor: This has 3 words",
                    "Very Important Key Point: This has 4 words (max)"
                ]
            },
            # Test colon rule (should NOT apply - too many words)
            {
                "layout": "TITLE_CONTENT",
                "title": "Colon Rule - No Formatting (>4 words)",
                "content": [
                    "This is more than four words before colon: Should NOT be bold",
                    "Regular bullet without special formatting",
                    "Another: Regular text"
                ]
            },
            # Test dash rule (1 word)
            {
                "layout": "TITLE_CONTENT",
                "title": "Dash Rule - Single Word",
                "content": [
                    "Goal - This should have 'Goal -' in bold",
                    "Note - Only the first part should be bold",
                    "Warning - Everything before dash is bold"
                ]
            },
            # Test dash rule (2-4 words)
            {
                "layout": "TITLE_CONTENT",
                "title": "Dash Rule - Multiple Words",
                "content": [
                    "Key Point - This should work with 2 words",
                    "Important Note - This has 2 words before dash",
                    "Critical Success Factor - This has 3 words",
                    "Very Important Key Point - This has 4 words (max)"
                ]
            },
            # Test dash rule (should NOT apply - too many words)
            {
                "layout": "TITLE_CONTENT",
                "title": "Dash Rule - No Formatting (>4 words)",
                "content": [
                    "This is more than four words before dash - Should NOT be bold",
                    "Regular bullet without special formatting",
                    "Another - Regular text"
                ]
            },
            # Mixed: colon takes precedence
            {
                "layout": "TITLE_CONTENT",
                "title": "Mixed Rules - Colon Takes Precedence",
                "content": [
                    "Key Point: This has both - but colon wins",
                    "Note - This only has dash, so dash rule applies",
                    "Warning: Colon comes first - so colon rule applies"
                ]
            },
            # Edge cases
            {
                "layout": "TITLE_CONTENT",
                "title": "Edge Cases",
                "content": [
                    "API: Application Programming Interface",
                    "Q - What is this?",
                    "A: This is the answer",
                    "FYI - For your information",
                    "No formatting here at all",
                    "Multiple-Word-Name: Should work with hyphens",
                    "Item 1 - Simple dash formatting"
                ]
            },
            # Thank you slide
            {
                "layout": "TITLE",
                "title": "Test Complete!",
                "subtitle": "Review the bullets to verify formatting"
            }
        ],
        "output": {
            "filename": "test_bullet_splitting.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("=" * 70)
    print("BULLET SPLITTING TEST - COLON AND DASH RULES")
    print("=" * 70)

    print("\nCreating deck specification...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)
    print(f"  Title: {deck_spec.title}")
    print(f"  Slides: {len(deck_spec.slides)}")

    print("\nRULES BEING TESTED:")
    print("  1. COLON RULE: 1-4 words + ':' → Bold")
    print("     Example: 'Key Point: text' → 'Key Point:' is bold")
    print("\n  2. DASH RULE: 1-4 words + ' - ' → Bold")
    print("     Example: 'Key Point - text' → 'Key Point -' is bold")
    print("\n  3. PRECEDENCE: Colon rule checked first, then dash rule")
    print("     Example: 'Note: text - more' → 'Note:' is bold (colon wins)")

    print("\nGenerating presentation...")
    renderer = PresentationRenderer()
    result = await renderer.generate_presentation(deck_spec)

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

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
            print(f"\n✅ PRESENTATION CREATED SUCCESSFULLY!")
            print(f"\nPlease open the file to verify bullet formatting:")
            print(f"   {output_path}")
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

    print("=" * 70)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_bullet_splitting())
    exit(0 if success else 1)
