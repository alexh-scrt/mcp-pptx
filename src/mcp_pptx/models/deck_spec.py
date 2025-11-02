"""Deck specification models."""

import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator

from .theme_spec import ThemeSpec
# Claude default output: /mnt/user-data/outputs/
CLAUDE_DEFAULT_OUTPUT_DIR = '/mnt/user-data/outputs/'
# Default output directory: use env var or fallback to user's home directory
DEFAULT_OUTPUT_DIR = os.getenv('OUTPUT_DIR', str(Path.home() / 'pptx-output'))
# DEFAULT_OUTPUT_DIR = os.getenv('OUTPUT_DIR', CLAUDE_DEFAULT_OUTPUT_DIR)

class LayoutType(str, Enum):
    """Available slide layout types."""

    TITLE = "TITLE"
    TITLE_CONTENT = "TITLE_CONTENT"
    SECTION = "SECTION"
    TWO_COL = "TWO_COL"
    IMAGE_FOCUS = "IMAGE_FOCUS"
    TABLE = "TABLE"
    CHART = "CHART"
    CODE = "CODE"
    BLANK = "BLANK"


class ContentType(str, Enum):
    """Content types for slide elements."""

    TEXT = "text"
    BULLETS = "bullets"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    CODE = "code"


class ImageSpec(BaseModel):
    """Image specification."""
    
    url: str = Field(..., description="Image URL or local path")
    alt_text: Optional[str] = Field(None, description="Alt text for accessibility")
    caption: Optional[str] = Field(None, description="Image caption")
    width: Optional[int] = Field(None, description="Desired width in pixels")
    height: Optional[int] = Field(None, description="Desired height in pixels")


class TableSpec(BaseModel):
    """Table specification."""
    
    headers: List[str] = Field(..., description="Table column headers")
    rows: List[List[str]] = Field(..., description="Table data rows")
    style: Optional[str] = Field("default", description="Table style")


class ChartSpec(BaseModel):
    """Chart specification."""

    type: str = Field(..., description="Chart type (bar, line, pie, etc.)")
    title: Optional[str] = Field(None, description="Chart title")
    data: Dict[str, Any] = Field(..., description="Chart data")
    x_axis_label: Optional[str] = Field(None, description="X-axis label")
    y_axis_label: Optional[str] = Field(None, description="Y-axis label")


class CodeSpec(BaseModel):
    """Code block specification."""

    code: str = Field(..., description="Code content to display")
    language: Optional[str] = Field(None, description="Programming language (python, bash, javascript, etc.)")
    title: Optional[str] = Field(None, description="Optional title for the code block")
    line_numbers: bool = Field(False, description="Whether to show line numbers")


class ContentPosition(str, Enum):
    """Position for content placement."""

    TITLE = "title"
    SUBTITLE = "subtitle"
    BODY = "body"


class SlideContent(BaseModel):
    """Content for a slide element."""

    type: ContentType = Field(ContentType.TEXT, description="Type of content (defaults to 'text' if not specified)")
    text: Optional[str] = Field(None, description="Text content")
    bullets: Optional[List[str]] = Field(None, description="Bullet points")
    image: Optional[ImageSpec] = Field(None, description="Image specification")
    table: Optional[TableSpec] = Field(None, description="Table specification")
    chart: Optional[ChartSpec] = Field(None, description="Chart specification")
    code: Optional[Union[CodeSpec, str]] = Field(None, description="Code specification or plain code string")
    position: Optional[ContentPosition] = Field(None, description="Position where content should be placed (title, subtitle, or body)")
    # Special fields for two-column layouts
    left: Optional[List[str]] = Field(None, description="Left column content for TWO_COL layout")
    right: Optional[List[str]] = Field(None, description="Right column content for TWO_COL layout")


class SlideSpec(BaseModel):
    """Specification for a single slide."""

    title: Optional[str] = Field(None, description="Slide title")
    subtitle: Optional[str] = Field(None, description="Slide subtitle")
    layout: LayoutType = Field(LayoutType.TITLE_CONTENT, description="Slide layout")
    content: List[SlideContent] = Field(default_factory=list, description="Slide content")
    speaker_notes: Optional[str] = Field(None, description="Speaker notes")

    @field_validator('layout', mode='before')
    @classmethod
    def normalize_layout(cls, v: Any) -> str:
        """Normalize layout to uppercase enum values."""
        if isinstance(v, str):
            # Convert to uppercase and replace hyphens/spaces with underscores
            normalized = v.upper().replace('-', '_').replace(' ', '_')
            return normalized
        return v

    @field_validator('content', mode='before')
    @classmethod
    def normalize_content(cls, v: Any) -> List[Dict[str, Any]]:
        """Normalize content to always be a list and handle various input formats."""
        # Handle special case: dict with 'left' and 'right' keys (TWO_COL layout)
        if isinstance(v, dict) and ('left' in v or 'right' in v):
            # This is two-column content - wrap it in a list as a single content item
            normalized_item = dict(v)
            # Ensure it has a type field
            if 'type' not in normalized_item:
                normalized_item['type'] = 'text'  # Default type
            return [normalized_item]

        # If content is a single dict (not two-column), wrap it in a list
        if isinstance(v, dict):
            v = [v]

        # If not a list at this point, return as-is and let Pydantic handle validation
        if not isinstance(v, list):
            return v

        # Normalize each content item
        normalized = []
        for item in v:
            if isinstance(item, dict):
                # Create a copy to avoid modifying the original
                normalized_item = dict(item)

                # Handle 'items' field name - convert to 'bullets'
                if 'items' in normalized_item and 'bullets' not in normalized_item:
                    normalized_item['bullets'] = normalized_item.pop('items')

                # Ensure type field exists with a default
                if 'type' not in normalized_item:
                    # Infer type based on content
                    if 'bullets' in normalized_item or 'items' in normalized_item:
                        normalized_item['type'] = 'bullets'
                    elif 'left' in normalized_item or 'right' in normalized_item:
                        normalized_item['type'] = 'text'  # Two-column content
                    else:
                        normalized_item['type'] = 'text'  # Default

                normalized.append(normalized_item)
            elif isinstance(item, str):
                # Convert plain strings to SlideContent objects
                # Skip empty strings
                if item.strip():
                    normalized.append({
                        'type': 'text',
                        'text': item
                    })
            else:
                normalized.append(item)

        return normalized


class OutputSpec(BaseModel):
    """Output specification."""

    filename: Optional[str] = Field(None, description="Output filename (auto-generated if not provided)")
    directory: str = Field(default_factory=lambda: DEFAULT_OUTPUT_DIR, description="Output directory")
    format: str = Field("pptx", description="Output format")


class FooterSpec(BaseModel):
    """Footer specification."""
    
    text: Optional[str] = Field(None, description="Footer text")
    show_slide_numbers: bool = Field(True, description="Show slide numbers")
    show_date: bool = Field(False, description="Show date")


class DeckSpec(BaseModel):
    """Complete deck specification."""
    
    title: str = Field(..., description="Presentation title")
    subtitle: Optional[str] = Field(None, description="Presentation subtitle")
    author: Optional[str] = Field(None, description="Presentation author")
    theme: ThemeSpec = Field(..., description="Theme specification")
    slides: List[SlideSpec] = Field(..., min_items=1, description="Slide specifications")
    output: OutputSpec = Field(default_factory=OutputSpec, description="Output specification")
    footer: Optional[FooterSpec] = Field(None, description="Footer specification")


class ValidationResult(BaseModel):
    """Result of deck validation."""
    
    valid: bool = Field(..., description="Whether the deck is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")