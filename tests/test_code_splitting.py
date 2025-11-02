#!/usr/bin/env python3
"""Test code splitting across multiple slides."""

import asyncio
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.mcp_pptx.models.deck_spec import DeckSpec
from src.mcp_pptx.rendering.renderer import PresentationRenderer
from src.mcp_pptx.rendering.content_fillers import ContentFiller


def test_split_logic():
    """Test the code splitting logic."""
    filler = ContentFiller()

    # Create a code sample with 50 lines
    code_50_lines = '\n'.join([f"line_{i} = 'This is line number {i}'" for i in range(1, 51)])

    print("=" * 70)
    print("CODE SPLITTING LOGIC TEST")
    print("=" * 70)

    print(f"\nOriginal code: {len(code_50_lines.split(chr(10)))} lines")

    chunks = filler._split_code_into_chunks(code_50_lines, max_lines_per_slide=25)

    print(f"Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks, 1):
        lines = chunk.split('\n')
        print(f"  Chunk {i}: {len(lines)} lines")
        print(f"    First line: {lines[0]}")
        print(f"    Last line:  {lines[-1]}")

    return chunks


async def test_code_splitting_presentation():
    """Create a presentation demonstrating code splitting."""

    # Generate a long code sample
    long_code = '''#!/usr/bin/env python3
"""
Complete User Management System
This is a comprehensive example showing a full user management implementation.
"""

import asyncio
import hashlib
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User role enumeration."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


@dataclass
class User:
    """User data model with comprehensive fields."""
    id: int
    username: str
    email: str
    password_hash: str
    role: UserRole = UserRole.USER
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True
    login_attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == self.password_hash


class UserRepository:
    """Repository for user data access."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.cache = {}
        logger.info("UserRepository initialized")

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID with caching."""
        if user_id in self.cache:
            logger.debug(f"Cache hit for user {user_id}")
            return self.cache[user_id]

        query = "SELECT * FROM users WHERE id = ? AND is_active = 1"
        result = await self.db.execute(query, (user_id,))

        if result:
            user = User(**result[0])
            self.cache[user_id] = user
            return user

        return None'''

    # Split the code
    filler = ContentFiller()
    code_chunks = filler._split_code_into_chunks(long_code, max_lines_per_slide=25)

    print(f"\n\nOriginal code has {len(long_code.split(chr(10)))} lines")
    print(f"Split into {len(code_chunks)} chunks for presentation")

    # Create slides for each chunk
    slides = [
        {
            "layout": "TITLE",
            "title": "Code Splitting Demo",
            "subtitle": f"Long code split across {len(code_chunks)} slides"
        }
    ]

    # Add a code slide for each chunk
    for i, chunk in enumerate(code_chunks, 1):
        slides.append({
            "layout": "CODE",
            "title": f"User Management System (Part {i}/{len(code_chunks)})",
            "content": [
                {
                    "type": "code",
                    "code": chunk,
                    "language": "python"
                }
            ]
        })

    # Add summary slide
    slides.append({
        "layout": "TITLE_CONTENT",
        "title": "Code Splitting Summary",
        "content": [
            f"Original code: {len(long_code.split(chr(10)))} lines",
            f"Split into: {len(code_chunks)} slides",
            f"Lines per slide: ~25 lines (configurable)",
            "Preserves: Indentation and formatting",
            "Ideal for: Long scripts, classes, or modules"
        ]
    })

    deck_spec_data = {
        "title": "Code Splitting Test",
        "subtitle": "Demonstrating automatic code splitting",
        "theme": {},
        "slides": slides,
        "output": {
            "filename": "test_code_splitting.pptx",
            "directory": str(Path.home() / "pptx-output")
        }
    }

    print("\nGenerating presentation...")
    deck_spec = DeckSpec.model_validate(deck_spec_data)
    renderer = PresentationRenderer()
    result = await renderer.generate_presentation(deck_spec)

    print("\n" + "=" * 70)
    print("RESULT")
    print("=" * 70)

    if result.get("ok"):
        print(f"✅ SUCCESS!")
        print(f"   Output: {result['output']}")
        print(f"   Slides: {result['slides_generated']}")
        print(f"   Code slides: {len(code_chunks)}")

        output_path = Path(result['output'])
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024
            print(f"   File size: {file_size:.1f} KB")
            print(f"\n✅ CODE SPLITTING TEST PASSED!")
            print(f"\n   {output_path}")
        else:
            print(f"\n❌ ERROR: Output file not found")
            return False
    else:
        print(f"❌ FAILED: {result.get('error')}")
        return False

    print("=" * 70)
    return True


if __name__ == "__main__":
    # Test the splitting logic
    test_split_logic()

    # Create presentation with split code
    success = asyncio.run(test_code_splitting_presentation())
    exit(0 if success else 1)
