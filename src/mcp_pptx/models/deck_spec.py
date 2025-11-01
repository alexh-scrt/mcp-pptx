"""Deck specification models."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from .theme_spec import ThemeSpec


class LayoutType(str, Enum):
    """Available slide layout types."""
    
    TITLE = "TITLE"
    TITLE_CONTENT = "TITLE_CONTENT"
    SECTION = "SECTION"
    TWO_COL = "TWO_COL"
    IMAGE_FOCUS = "IMAGE_FOCUS"
    TABLE = "TABLE"
    CHART = "CHART"
    BLANK = "BLANK"


class ContentType(str, Enum):
    """Content types for slide elements."""
    
    TEXT = "text"
    BULLETS = "bullets"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"


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


class SlideContent(BaseModel):
    """Content for a slide element."""
    
    type: ContentType = Field(..., description="Type of content")
    text: Optional[str] = Field(None, description="Text content")
    bullets: Optional[List[str]] = Field(None, description="Bullet points")
    image: Optional[ImageSpec] = Field(None, description="Image specification")
    table: Optional[TableSpec] = Field(None, description="Table specification")
    chart: Optional[ChartSpec] = Field(None, description="Chart specification")


class SlideSpec(BaseModel):
    """Specification for a single slide."""
    
    title: Optional[str] = Field(None, description="Slide title")
    subtitle: Optional[str] = Field(None, description="Slide subtitle")
    layout: LayoutType = Field(LayoutType.TITLE_CONTENT, description="Slide layout")
    content: List[SlideContent] = Field(default_factory=list, description="Slide content")
    speaker_notes: Optional[str] = Field(None, description="Speaker notes")


class OutputSpec(BaseModel):
    """Output specification."""
    
    filename: Optional[str] = Field(None, description="Output filename (auto-generated if not provided)")
    directory: str = Field("/mnt/user-data/outputs", description="Output directory")
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