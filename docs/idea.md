* **MCP (Model Context Protocol) Python SDK** for the server
* **python-pptx** to render `.pptx` using a **real `.potx` theme** (master layouts, placeholders, colors, fonts)
* **pydantic** to validate the deck spec
* **requests** to fetch remote images
* A small **layout engine** for consistent placement

---

# 1) Project layout

```
slidesmith-py/
├─ src/
│  ├─ server.py                 # MCP server (stdio)
│  ├─ renderer.py               # PPTX renderer & layout helpers
│  ├─ theme.py                  # Theme + template handling
│  ├─ models.py                 # Pydantic DeckSpec schema
│  ├─ assets.py                 # Image fetching/optimization
│  └─ utils.py                  # Common utilities
├─ themes/
│  ├─ nice-actimize.potx        # Your branded PowerPoint template (master layouts)
│  └─ default.potx
├─ examples/
│  └─ nice_actimize_deck.json   # Example DeckSpec (NICE Actimize)
├─ pyproject.toml
└─ README.md
```

> 🔑 **Why `.potx` matters**: python-pptx can’t “paint” fancy themes from scratch, but it *can* open a `.potx` that already has the blue header bar, logo in master, fonts, color scheme, named master layouts, etc. That’s how we get true brand fidelity.

---

# 2) Dependencies

```toml
# pyproject.toml
[project]
name = "slidesmith-py"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
  "modelcontextprotocol==0.1.4",
  "python-pptx==0.6.23",
  "pydantic==2.9.2",
  "requests==2.32.3",
  "pillow==10.4.0",
]

[project.scripts]
slidesmith = "src.server:main"
```

Install:

```bash
pip install -e .
```

---

# 3) DeckSpec schema (Pydantic)

```python
# src/models.py
from pydantic import BaseModel, HttpUrl, Field, field_validator
from typing import List, Literal, Optional, Union

Placement = Literal["left", "right", "top", "bottom", "center", "grid", "full"]

class ImageSpec(BaseModel):
    src: Union[str, HttpUrl]                 # "url:https://..." or "file:/path/to/file" or local "assets/logo.png"
    alt: Optional[str] = None
    placement: Placement = "right"
    max_width: Optional[int] = None          # px at 96 DPI; or we'll scale to fit placeholder
    max_height: Optional[int] = None

class TableSpec(BaseModel):
    columns: List[str]
    rows: List[List[str]]

class SlideSpec(BaseModel):
    layout: Literal[
        "TITLE", "SECTION", "TITLE_CONTENT", "TWO_COL",
        "IMAGE_FOCUS", "IMAGE_GRID", "TABLE", "QUOTE", "TIMELINE"
    ]
    title: str
    subtitle: Optional[str] = None
    bullets: Optional[List[str]] = None
    images: Optional[List[ImageSpec]] = None
    table: Optional[TableSpec] = None
    notes: Optional[str] = None
    layout_hint: Optional[str] = None  # e.g., "image-right-40", "two-col-60-40"

class ThemeSpec(BaseModel):
    template: str = "themes/default.potx"     # path to .potx
    accent_color: Optional[str] = None        # "#005596"
    logo: Optional[str] = None                # asset path or url:
    footer: Optional[str] = None              # "© NICE Actimize"

    @field_validator("accent_color")
    @classmethod
    def norm_hex(cls, v):
        if not v:
            return v
        v = v.strip()
        if not v.startswith("#"):
            v = f"#{v}"
        if len(v) != 7:
            raise ValueError("accent_color must be #RRGGBB")
        return v

class OutputSpec(BaseModel):
    filename: str = "deck.pptx"

class DeckSpec(BaseModel):
    title: str
    output: OutputSpec
    theme: ThemeSpec
    slides: List[SlideSpec]
```

---

# 4) Theme loader

```python
# src/theme.py
from pptx import Presentation
from .models import ThemeSpec

def load_template(theme: ThemeSpec) -> Presentation:
    """
    Load the .potx template with master layouts.
    """
    prs = Presentation(theme.template)
    return prs

def find_layout_by_name(prs: Presentation, name: str):
    """
    Resolve a layout by name. Your .potx should name layouts like:
    'TITLE', 'TITLE_CONTENT', 'TWO_COL', 'SECTION', etc.
    Fallback to index if name not found.
    """
    for layout in prs.slide_layouts:
        if layout.name.strip().upper() == name:
            return layout
    # Fallback: basic mapping by index (must match your potx)
    fallbacks = {
        "TITLE": 0,
        "SECTION": 2,
        "TITLE_CONTENT": 1,
        "TWO_COL": 3,
        "IMAGE_FOCUS": 5,
        "TABLE": 6,
        "QUOTE": 7
    }
    idx = fallbacks.get(name, 1)
    return prs.slide_layouts[idx]
```

> ⚠️ Open your `.potx` in PowerPoint and rename your custom layouts to match the names above. That gives you deterministic control here.

---

# 5) Image fetching & caching

```python
# src/assets.py
import os, hashlib, requests
from pathlib import Path
from typing import Tuple

ASSETS_DIR = Path("./.cache/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()

def fetch_asset(src: str) -> Path:
    """
    Supports:
      - url:https://...
      - file:/abs/path/to.png
      - relative path: assets/logo.png
    Returns a local Path to a file suitable for python-pptx add_picture.
    """
    if src.startswith("url:"):
        url = src[4:]
        fname = ASSETS_DIR / f"{_hash(url)}.bin"
        if not fname.exists():
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            fname.write_bytes(r.content)
        return fname

    if src.startswith("file:"):
        return Path(src[5:])

    return Path(src).resolve()
```

---

# 6) Renderer with real layouts

```python
# src/renderer.py
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx import Presentation
from typing import Optional, Tuple

from .models import DeckSpec, SlideSpec, ImageSpec
from .theme import load_template, find_layout_by_name
from .assets import fetch_asset

def _hex_to_rgb(hex_color: Optional[str]) -> Tuple[int,int,int]:
    if not hex_color: return (0, 85, 150)  # NICE blue fallback
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def _apply_footer(slide, text: Optional[str]):
    if not text:
        return
    tx = slide.shapes.add_textbox(Inches(0.3), Inches(6.9), Inches(9.2), Inches(0.4))
    tf = tx.text_frame
    tf.text = text
    p = tf.paragraphs[0]
    p.font.size = Pt(10)
    p.font.color.rgb = RGBColor(102, 102, 102)
    p.alignment = PP_ALIGN.CENTER

def _insert_images(slide, images: list[ImageSpec], placement: str):
    """
    Basic placement strategy. For complex themes, rely on
    image placeholders in the .potx and fill them instead.
    """
    if not images:
        return
    if placement in ("right", "left"):
        # Reserve half slide area for image
        x = Inches(5.5 if placement == "right" else 0.5)
        y = Inches(1.8)
        w = Inches(4.0)
        for img in images[:1]:
            path = fetch_asset(img.src)
            slide.shapes.add_picture(str(path), x, y, width=w)
    elif placement == "full":
        path = fetch_asset(images[0].src)
        slide.shapes.add_picture(str(path), Inches(0), Inches(0.4), width=Inches(10))
    else:
        # default center/grid
        x, y, w = Inches(1.0), Inches(2.0), Inches(8.0)
        path = fetch_asset(images[0].src)
        slide.shapes.add_picture(str(path), x, y, width=w)

def _fill_title(slide, title: str, subtitle: Optional[str] = None):
    # Rely on master placeholders when available
    try:
        slide.shapes.title.text = title
    except Exception:
        # Add a manual title
        tx = slide.shapes.add_textbox(Inches(0.6), Inches(0.6), Inches(8.8), Inches(0.8))
        tf = tx.text_frame
        tf.text = title
        tf.paragraphs[0].font.size = Pt(36)

    # Subtitle if placeholder exists
    if subtitle:
        # Try the standard subtitle placeholder index (varies by layout)
        for ph in slide.placeholders:
            if ph.placeholder_format.type == 1:  # SUBTITLE
                ph.text = subtitle
                return
        # else add manually
        tx2 = slide.shapes.add_textbox(Inches(0.6), Inches(1.4), Inches(8.8), Inches(0.6))
        tf2 = tx2.text_frame
        tf2.text = subtitle
        tf2.paragraphs[0].font.size = Pt(18)

def _fill_bullets(slide, bullets: list[str], left=Inches(0.6), top=Inches(2.0), w=Inches(4.7), h=Inches(3.8)):
    tx = slide.shapes.add_textbox(left, top, w, h)
    tf = tx.text_frame
    tf.clear()
    for i, b in enumerate(bullets):
        p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
        p.text = b
        p.level = 0
        p.font.size = Pt(18)

def render_deck(spec: DeckSpec) -> str:
    prs: Presentation = load_template(spec.theme)
    accent_rgb = _hex_to_rgb(spec.theme.accent_color)

    # TITLE slide
    first = spec.slides[0] if spec.slides else None

    for s in spec.slides:
        layout = find_layout_by_name(prs, s.layout)
        slide = prs.slides.add_slide(layout)
        _fill_title(slide, s.title, s.subtitle)
        if s.bullets:
            # Default: bullets left, image right
            _fill_bullets(slide, s.bullets)
        if s.images:
            placement = s.images[0].placement if s.images else "right"
            _insert_images(slide, s.images, placement)
        if s.notes:
            slide.notes_slide.notes_text_frame.text = s.notes
        _apply_footer(slide, spec.theme.footer)

    out = spec.output.filename
    prs.save(out)
    return out
```

---

# 7) MCP server (stdio)

```python
# src/server.py
import json, sys, traceback
from mcp import Server
from mcp.types import Tool, TextContent
from .models import DeckSpec
from .renderer import render_deck
from .theme import load_template
from pathlib import Path

server = Server("slidesmith-py")

@server.list_tools()
def _tools():
    return [
        Tool(name="generate_pptx", description="Render a PowerPoint from a DeckSpec JSON.", inputSchema={"type":"object","properties":{"deck_spec":{"type":"object"}},"required":["deck_spec"]}),
        Tool(name="list_templates", description="List available POTX templates.", inputSchema={"type":"object","properties":{}}),
        Tool(name="validate_deck_spec", description="Validate a DeckSpec and echo issues.", inputSchema={"type":"object","properties":{"deck_spec":{"type":"object"}},"required":["deck_spec"]})
    ]

@server.call_tool()
def _call(tool_name: str, arguments: dict):
    try:
        if tool_name == "list_templates":
            templates = [str(p) for p in Path("themes").glob("*.potx")]
            return [TextContent(text=json.dumps({"templates": templates}, indent=2))]

        if tool_name == "validate_deck_spec":
            DeckSpec.model_validate(arguments["deck_spec"])
            return [TextContent(text=json.dumps({"ok": True}, indent=2))]

        if tool_name == "generate_pptx":
            spec = DeckSpec.model_validate(arguments["deck_spec"])
            out = render_deck(spec)
            return [TextContent(text=json.dumps({"ok": True, "output": out}, indent=2))]

        return [TextContent(text=json.dumps({"ok": False, "error": "Unknown tool"}, indent=2))]
    except Exception as e:
        return [TextContent(text=json.dumps({"ok": False, "error": str(e), "trace": traceback.format_exc()}, indent=2))]

def main():
    server.run_stdio()

if __name__ == "__main__":
    main()
```

> This runs over **stdio**, as MCP expects. Your client (e.g., your LLM runtime) will connect and call the tools `generate_pptx`, etc.

---

# 8) Provide a real `.potx` theme

Create **`themes/nice-actimize.potx`** with:

* Master slide: deep blue header bar (#005596), white body, grey footer
* Logo in master top-right
* Named layouts: `TITLE`, `SECTION`, `TITLE_CONTENT`, `TWO_COL`, `IMAGE_FOCUS`, `TABLE`
* Proper text placeholders (title, subtitle, content left, image right, etc.)

> Open PowerPoint → View → Slide Master → **Rename** layouts (Home → Layout → right-click → Rename). Save as `.potx`.

---

# 9) Example DeckSpec (NICE Actimize)

```json
{
  "title": "NICE Actimize: Anti-Fraud & AML Overview",
  "output": { "filename": "nice_actimize.pptx" },
  "theme": {
    "template": "themes/nice-actimize.potx",
    "accent_color": "#005596",
    "logo": "assets/logo_nice_actimize.png",
    "footer": "© NICE Actimize"
  },
  "slides": [
    { "layout": "TITLE", "title": "NICE Actimize", "subtitle": "Unified Financial Crime Intelligence" },

    { "layout": "TITLE_CONTENT", "title": "1. Core Solutions",
      "bullets": [
        "AML – Monitoring, entity risk, compliance",
        "Enterprise Fraud Management – Real-time detection",
        "Markets Compliance – Trade & comms surveillance",
        "Investigation & Case Management – Unified workflows",
        "Data Intelligence – Enrichment & screening"
      ],
      "images": [
        {"src": "url:https://marvel-b1-cdn.bc0a.com/f00000000281080/www.niceactimize.com/resources/pages/xceed/aml/xceeddiagram.png", "placement": "right"}
      ]
    },

    { "layout": "TITLE_CONTENT", "title": "2. Platforms & Foundations",
      "bullets": [
        "X-Sight Platform – Cloud-scale, limitless data, ‘One Trust Score’",
        "Xceed FRAML – Unified Fraud + AML with AI and automation"
      ],
      "images": [
        {"src": "url:https://marvel-b1-cdn.bc0a.com/f00000000281080/www.niceactimize.com/resources/pages/xsight/section-3-img.png", "placement": "right"}
      ]
    }
    // ... continue your 15 slides 1-per-section as before
  ]
}
```

---

# 10) How to run & call

**Run server:**

```bash
slidesmith  # or: python -m src.server
```

**MCP client side (pseudo):**

```json
{
  "type": "tools/call",
  "toolName": "generate_pptx",
  "arguments": { "deck_spec": { ... DeckSpec JSON ... } }
}
```

**Response:**

```json
{ "ok": true, "output": "nice_actimize.pptx" }
```

---

## Notes & Enhancements

* **Image placeholders**: For pixel-perfect placement, add image placeholders to your `.potx` layouts. In `renderer.py`, locate placeholder by type/index and call `placeholder.insert_picture(path)`. That will auto-fit to placeholder bounds, preserving your design grid.
* **Tables & charts**: `python-pptx` supports tables well; charts require more setup but are feasible. For charts, prepare a layout with a chart placeholder and fill it.
* **Fonts**: python-pptx can set font names/sizes, but true font embedding is handled by the client machine; ensure corporate fonts are installed on the presentation system (or stick to system fonts like Calibri/Arial).
* **Validation**: Extend `validate_deck_spec` to check that referenced layouts exist in the `.potx`, that images are reachable, etc., and return actionable errors.
* **Asset policy**: For production, add caching, size limits, and content-type checks when fetching URLs.

---
