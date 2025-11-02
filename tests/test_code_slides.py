#!/usr/bin/env python3
"""Test script for CODE slide layout."""

import asyncio
import json
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer


# Sample code examples
PYTHON_CODE = '''def fibonacci(n):
    """Calculate fibonacci sequence up to n."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])

    return fib

# Test the function
print(fibonacci(10))
'''

BASH_CODE = '''#!/bin/bash
# Deploy script for production

echo "Starting deployment..."

# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart service
sudo systemctl restart myapp

echo "Deployment complete!"
'''

LONG_PYTHON_CODE = '''import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User data model."""
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


class UserService:
    """Service for managing users."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.cache = {}

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        # Check cache first
        if user_id in self.cache:
            logger.debug(f"Cache hit for user {user_id}")
            return self.cache[user_id]

        # Query database
        query = "SELECT * FROM users WHERE id = ?"
        result = await self.db.execute(query, (user_id,))
'''


async def test_code_slides():
    """Test CODE slide layout with various code examples."""

    deck_spec_data = {
        "title": "Code Slide Test",
        "subtitle": "Testing CODE layout with various code examples",
        "theme": {},  # Use default theme
        "slides": [
            # Title slide
            {
                "layout": "TITLE",
                "title": "Code Slide Test",
                "subtitle": "Demonstrating CODE Layout"
            },
            # Introduction
            {
                "layout": "TITLE_CONTENT",
                "title": "What We'll Test",
                "content": [
                    "Short Python code example",
                    "Bash script example",
                    "Long code that requires splitting",
                    "Code with optional title and language"
                ]
            },
            # Python code example
            {
                "layout": "CODE",
                "title": "Python Fibonacci Function",
                "content": [
                    {
                        "type": "code",
                        "code": PYTHON_CODE,
                        "language": "python",
                        "title": "Fibonacci Generator"
                    }
                ]
            },
            # Bash script example
            {
                "layout": "CODE",
                "title": "Deployment Script",
                "content": [
                    {
                        "type": "code",
                        "code": BASH_CODE,
                        "language": "bash"
                    }
                ]
            },
            # Long code example (will test the splitting logic)
            {
                "layout": "CODE",
                "title": "User Service Class",
                "content": [
                    {
                        "type": "code",
                        "code": LONG_PYTHON_CODE,
                        "language": "python",
                        "title": "User Management Service"
                    }
                ]
            },
            # Code without title (simple format)
            {
                "layout": "CODE",
                "content": [
                    {
                        "type": "code",
                        "code": "print('Hello, World!')\nprint('This is a simple example')"
                    }
                ]
            },
            # Summary
            {
                "layout": "TITLE_CONTENT",
                "title": "Code Slide Features",
                "content": [
                    "Format: Courier New font, 24pt for readability",
                    "Background: Light gray (#F5F5F5) for code box",
                    "Layout: White slide background, no title bar",
                    "Support: Python, Bash, JavaScript, and more",
                    "Splitting: Long code can be split across slides"
                ]
            },
            # Thank you
            {
                "layout": "TITLE",
                "title": "Test Complete",
                "subtitle": "CODE slides are working!"
            }
        ],
        "output": {
            "filename": "test_code_slides.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("=" * 70)
    print("CODE SLIDE TEST")
    print("=" * 70)

    print("\nCreating deck specification...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)
    print(f"  Title: {deck_spec.title}")
    print(f"  Slides: {len(deck_spec.slides)}")

    print("\nCODE SLIDE FEATURES:")
    print("  • Font: Courier New, 24pt")
    print("  • Background: Light gray (#F5F5F5) code box")
    print("  • Slide background: White")
    print("  • Formatting: Preserves indentation and line breaks")
    print("  • Languages: Python, Bash, JavaScript, etc.")
    print("  • Optional: Title and language metadata")

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
            print(f"\n✅ CODE SLIDE TEST PASSED!")
            print(f"\nOpen the presentation to verify code formatting:")
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
    success = asyncio.run(test_code_slides())
    exit(0 if success else 1)
