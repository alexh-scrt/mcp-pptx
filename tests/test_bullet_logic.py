#!/usr/bin/env python3
"""Unit test for bullet splitting logic."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_pptx.rendering.content_fillers import ContentFiller


def test_colon_rule():
    """Test the colon rule."""
    filler = ContentFiller()

    print("=" * 70)
    print("TESTING COLON RULE (_split_bullet_with_colon)")
    print("=" * 70)

    test_cases = [
        # (input, expected_bold, expected_plain, description)
        ("Goal: Achieve success", "Goal: ", "Achieve success", "1 word + colon"),
        ("Key Point: Important info", "Key Point: ", "Important info", "2 words + colon"),
        ("Critical Success Factor: Details here", "Critical Success Factor: ", "Details here", "3 words + colon"),
        ("Very Important Key Point: More text", "Very Important Key Point: ", "More text", "4 words + colon (max)"),
        ("This is way too many words before colon: Text", None, None, "5+ words (should fail)"),
        ("No colon here", None, None, "No colon"),
        ("API: Application Programming Interface", "API: ", "Application Programming Interface", "Acronym + colon"),
    ]

    passed = 0
    failed = 0

    for i, (input_text, expected_bold, expected_plain, description) in enumerate(test_cases, 1):
        bold, plain = filler._split_bullet_with_colon(input_text)

        success = (bold == expected_bold and plain == expected_plain)
        status = "✅ PASS" if success else "❌ FAIL"

        print(f"\nTest {i}: {description}")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: bold='{expected_bold}', plain='{expected_plain}'")
        print(f"  Got:      bold='{bold}', plain='{plain}'")
        print(f"  {status}")

        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{'-' * 70}")
    print(f"Colon Rule: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0


def test_dash_rule():
    """Test the dash rule."""
    filler = ContentFiller()

    print("\n" + "=" * 70)
    print("TESTING DASH RULE (_split_bullet_with_dash)")
    print("=" * 70)

    test_cases = [
        # (input, expected_bold, expected_plain, description)
        ("Goal - Achieve success", "Goal - ", "Achieve success", "1 word + dash"),
        ("Key Point - Important info", "Key Point - ", "Important info", "2 words + dash"),
        ("Critical Success Factor - Details here", "Critical Success Factor - ", "Details here", "3 words + dash"),
        ("Very Important Key Point - More text", "Very Important Key Point - ", "More text", "4 words + dash (max)"),
        ("This is way too many words before dash - Text", None, None, "5+ words (should fail)"),
        ("No dash here", None, None, "No dash"),
        ("Single-dash without spaces-here", None, None, "Dash without spaces"),
        ("Q - What is this?", "Q - ", "What is this?", "Single letter + dash"),
        ("FYI - For your information", "FYI - ", "For your information", "Acronym + dash"),
    ]

    passed = 0
    failed = 0

    for i, (input_text, expected_bold, expected_plain, description) in enumerate(test_cases, 1):
        bold, plain = filler._split_bullet_with_dash(input_text)

        success = (bold == expected_bold and plain == expected_plain)
        status = "✅ PASS" if success else "❌ FAIL"

        print(f"\nTest {i}: {description}")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: bold='{expected_bold}', plain='{expected_plain}'")
        print(f"  Got:      bold='{bold}', plain='{plain}'")
        print(f"  {status}")

        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{'-' * 70}")
    print(f"Dash Rule: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0


def test_combined_rule():
    """Test the combined rule (colon takes precedence)."""
    filler = ContentFiller()

    print("\n" + "=" * 70)
    print("TESTING COMBINED RULE (_split_bullet_for_bold)")
    print("=" * 70)

    test_cases = [
        # (input, expected_bold, expected_plain, description)
        ("Goal: Achieve success", "Goal: ", "Achieve success", "Colon rule applies"),
        ("Goal - Achieve success", "Goal - ", "Achieve success", "Dash rule applies"),
        ("Note: This has both - but colon wins", "Note: ", "This has both - but colon wins", "Both present - colon wins"),
        ("Item - Has dash: and colon", "Item - Has dash: ", "and colon", "Both present - colon checked first and wins (4 words before colon)"),
        ("Regular bullet point", None, None, "No special formatting"),
        ("This is five words count: Should not format", None, None, "5 words + colon (should fail)"),
        ("This is five words total - Should not format", None, None, "5 words + dash (should fail)"),
        ("Way too many words - Still formats", "Way too many words - ", "Still formats", "4 words + dash (should work)"),
    ]

    passed = 0
    failed = 0

    for i, (input_text, expected_bold, expected_plain, description) in enumerate(test_cases, 1):
        bold, plain = filler._split_bullet_for_bold(input_text)

        success = (bold == expected_bold and plain == expected_plain)
        status = "✅ PASS" if success else "❌ FAIL"

        print(f"\nTest {i}: {description}")
        print(f"  Input:    '{input_text}'")
        print(f"  Expected: bold='{expected_bold}', plain='{expected_plain}'")
        print(f"  Got:      bold='{bold}', plain='{plain}'")
        print(f"  {status}")

        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n{'-' * 70}")
    print(f"Combined Rule: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    return failed == 0


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("BULLET SPLITTING LOGIC TESTS")
    print("█" * 70)

    colon_pass = test_colon_rule()
    dash_pass = test_dash_rule()
    combined_pass = test_combined_rule()

    print("\n" + "█" * 70)
    print("FINAL RESULTS")
    print("█" * 70)
    print(f"Colon Rule:    {'✅ PASSED' if colon_pass else '❌ FAILED'}")
    print(f"Dash Rule:     {'✅ PASSED' if dash_pass else '❌ FAILED'}")
    print(f"Combined Rule: {'✅ PASSED' if combined_pass else '❌ FAILED'}")

    if colon_pass and dash_pass and combined_pass:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        exit(1)
