# MCP-PPTX Server Architecture v1.1

## Design Philosophy

**Core Principles:**
1. **Composable Tools** - Claude orchestrates multiple focused tools
2. **Lightweight Theme Extraction** - Colors, fonts, logo only
3. **Claude as Content Creator** - Server is a rendering engine
4. **Modern Web Support** - Playwright for JS-heavy sites with fallback
5. **Minimal Caching** - Only downloaded assets (24-hour TTL)
6. **Graceful Degradation** - Always produce output + warnings
7. **Smart Formatting** - Automatic bullet styling and code rendering
8. **Default Theme** - Secret AI theme when no theme specified

---

## Tool Design

### **Tool 1: `scrape_theme`**
```python
Input:
  - url: str
  - extract_logo: bool = True
  - selector_hints: Optional[dict] = None  # e.g., {"logo": ".navbar img"}

Output:
  {
    "colors": {
      "primary": "#005596",
      "secondary": "#0A77C0", 
      "accent": "#FF5733",
      "background": "#FFFFFF",
      "text": "#333333"
    },
    "fonts": {
      "heading": "Montserrat",
      "body": "Open Sans"
    },
    "logo": {
      "url": "https://...",
      "cached_path": "/cache/assets/abc123.png"
    },
    "warnings": ["Could not extract secondary color, using derived shade"]
  }
```

**Extraction Strategy:**
- Launch Playwright → navigate to URL → wait for network idle
- Parse computed styles from root elements (`:root`, `body`, `h1`)
- Extract CSS variables (`--primary-color`, etc.)
- Find logo via common selectors: `header img`, `.logo`, `nav img[alt*="logo"]`
- Extract dominant colors from hero section if CSS extraction fails
- Map web fonts to PowerPoint-safe alternatives (Montserrat → Calibri Light)

---

### **Tool 2: `list_templates`**
```python
Input: (none)

Output:
  {
    "templates": [
      {
        "name": "secret_ai_default",
        "type": "theme",
        "path": "themes/default_theme.json",
        "layouts": ["TITLE", "TITLE_CONTENT", "SECTION", "TWO_COL", "CODE", "IMAGE_FOCUS", "TABLE", "CHART", "BLANK"],
        "description": "Default Secret AI theme (Red, Cyan, White)",
        "colors": {
          "primary": "#E3342F",
          "secondary": "#FFE9D3",
          "accent": "#1CCBD0",
          "background": "#FFFFFF",
          "text": "#111827"
        },
        "fonts": {
          "heading": "Calibri",
          "body": "Tahoma"
        }
      },
      {
        "name": "custom-template",
        "type": "potx",
        "path": "themes/custom-template.potx",
        "layouts": ["TITLE", "SECTION", "TITLE_CONTENT", "TWO_COL", "TABLE", "CHART"],
        "description": "PowerPoint template: custom-template"
      }
    ]
  }
```

**Purpose:** Let Claude see available templates and their capabilities. Includes default Secret AI theme as primary option.

---

### **Tool 3: `validate_deck`**
```python
Input:
  - deck_spec: dict  # The full DeckSpec JSON

Output:
  {
    "valid": true,
    "errors": [],
    "warnings": [
      "Slide 3: Layout 'FANCY_LAYOUT' not found in template, will use TITLE_CONTENT",
      "Slide 5: Image URL https://... returned 404, will use placeholder"
    ],
    "suggestions": [
      "Consider using 'TWO_COL' layout for slide 4 to better accommodate image+bullets"
    ]
  }
```

**Validation Checks:**
- Pydantic schema validation
- Check if layouts exist in specified template
- Verify image URLs are reachable (HEAD request)
- Warn about oversized images
- Suggest layout improvements based on content

---

### **Tool 4: `generate_presentation`**
```python
Input:
  - deck_spec: dict  # The full DeckSpec JSON

Output:
  {
    "ok": true,
    "output": "/mnt/user-data/outputs/nice_actimize_20251021_143022.pptx",
    "slides_generated": 15,
    "warnings": [
      "Slide 7: Image 'hero.png' not found, used placeholder",
      "Slide 12: Chart series 'Revenue' has only 2 data points, may look sparse"
    ],
    "assets_downloaded": [
      "logo.png (cached)",
      "diagram.svg (converted to PNG)"
    ]
  }
```

**Rendering Process:**
1. Load `.potx` template
2. For each slide:
   - Find layout (with fallback)
   - Fill title/subtitle
   - Add bullets, images, tables, charts
   - Apply theme colors
   - Add speaker notes
3. Apply footer to all slides
4. Save to `/mnt/user-data/outputs/`
5. Return file path + warnings

---

### **Tool 5: `merge_themes`** (Optional Enhancement)
```python
Input:
  - themes: List[ThemeSpec]
  - priority: "first" | "balanced"

Output:
  {
    "merged_theme": { ... },
    "decisions": [
      "Primary color from theme 1",
      "Fonts from theme 2",
      "Logo from theme 1"
    ]
  }
```

**Use Case:** Claude scrapes multiple sites and combines themes.

---

## New Features (v1.1)

### **CODE Slide Layout**

**Purpose:** Display source code with proper monospace formatting and syntax-appropriate styling.

**Features:**
- Font: Courier New, 20pt
- Code box background: Light gray (#F5F5F5)
- Slide background: White (no title bar)
- Preserves indentation and line breaks
- Auto-splits long code across multiple slides (>15 lines)

**Usage:**
```json
{
  "layout": "CODE",
  "title": "Python Example",
  "content": [
    {
      "type": "code",
      "code": "def hello():\n    print('Hello, World!')",
      "language": "python",
      "title": "Optional code block title"
    }
  ]
}
```

**Auto-Splitting:**
- Splits code into chunks of 15 lines per slide
- Configurable via `_split_code_into_chunks(max_lines_per_slide=15)`
- Maintains proper formatting across slides
- Automatically creates continuation slides with part numbers

---

### **Smart Bullet Formatting**

**Purpose:** Automatically bold prefixes in bullet points for emphasis.

**Colon Rule** (Priority 1):
- Detects 1-4 words followed by `:`
- Makes prefix bold including the colon
- Example: "Goal: Achieve success" → **Goal:** Achieve success

**Dash Rule** (Priority 2):
- Detects 1-4 words followed by ` - ` (space-dash-space)
- Makes prefix bold including the dash
- Example: "Goal - Achieve success" → **Goal -** Achieve success

**Implementation:**
```python
_split_bullet_with_colon(bullet: str) -> tuple[str, str]
_split_bullet_with_dash(bullet: str) -> tuple[str, str]
_split_bullet_for_bold(bullet: str) -> tuple[str, str]  # Orchestrator
```

**Rules:**
- Colon rule checked first (higher priority)
- Only applies to prefixes of 1-4 words
- Both rules require exact patterns (no partial matches)
- Returns `(None, None)` if no rule matches

---

### **Default Secret AI Theme**

**Purpose:** Provide consistent branding when no theme is specified.

**Colors:**
- Primary (Red): #E3342F
- Secondary (Light Peach): #FFE9D3
- Accent (Cyan): #1CCBD0
- Background (White): #FFFFFF
- Text (Dark Gray): #111827

**Layout-Specific Backgrounds:**
- **TITLE**: Red background (#E3342F)
- **SECTION**: Rotating colors (Cyan → Red → Peach)
- **TITLE_CONTENT**: White background with red title bar
- **CODE**: White background (no title bar)
- **Other layouts**: White background with red title bar

**Auto-Application:**
- Automatically loaded from `themes/default_theme.json`
- Applied when `theme: {}` or no theme specified
- Can be overridden by scraped theme or template

---

## Component Architecture

### **1. Web Scraping Module** (`extraction/theme_extractor.py`)

```
ThemeExtractor
├─ launch_browser() → Playwright instance
├─ extract_colors(page) → dict
│   ├─ parse_css_variables()
│   ├─ parse_computed_styles()
│   └─ analyze_hero_image() [fallback]
├─ extract_fonts(page) → dict
│   ├─ get_computed_font_families()
│   └─ map_to_pptx_fonts()
└─ extract_logo(page, hints) → LogoSpec
    ├─ try_common_selectors()
    └─ download_and_cache()
```

**Font Mapping Strategy:**
```python
FONT_MAPPINGS = {
    "Montserrat": "Calibri Light",
    "Roboto": "Calibri",
    "Open Sans": "Arial",
    "Lato": "Calibri",
    "Poppins": "Gill Sans MT",
    # ... web font → PowerPoint-safe font
}
```

**Color Extraction Priority:**
1. CSS custom properties (`--primary-color`, `--brand-color`)
2. Computed styles on `:root`, `body`
3. Most common colors in hero section image
4. Fallback to sensible defaults

---

### **2. Rendering Engine** (`rendering/`)

```
Renderer
├─ renderer.py (orchestration + default theme loading)
├─ layouts.py (layout resolution + fallbacks)
├─ theme_applicator.py (apply colors, fonts, logos, backgrounds)
│   ├─ apply_slide_background() [TITLE, SECTION, CODE, content slides]
│   └─ add_title_bar_to_content_slide()
├─ content_fillers.py
│   ├─ _fill_title()
│   ├─ _fill_bullets()
│   │   ├─ _split_bullet_for_bold() [smart formatting orchestrator]
│   │   ├─ _split_bullet_with_colon() [colon rule]
│   │   └─ _split_bullet_with_dash() [dash rule]
│   ├─ _fill_code() [NEW - CODE slide rendering]
│   ├─ _split_code_into_chunks() [NEW - auto-split long code]
│   ├─ _fill_images()
│   ├─ _fill_table()
│   ├─ _fill_chart()
│   └─ _fill_two_column()
└─ placeholder_detector.py (find & fill placeholders)
```

**Graceful Degradation Rules:**

| Issue              | Fallback Strategy                  |
| ------------------ | ---------------------------------- |
| Layout not found   | Use `TITLE_CONTENT`                |
| Image 404          | Gray placeholder box with alt text |
| Font unavailable   | Use template default               |
| Chart data invalid | Skip chart, add note               |
| Too many bullets   | Paginate into multiple slides      |
| Oversized image    | Auto-scale to fit                  |

---

### **3. Asset Management** (`cache.py`)

```python
AssetCache
├─ download_image(url) → Path
│   ├─ Check if cached (sha256 hash of URL)
│   ├─ Download if missing
│   └─ Optimize (resize if >2MB, convert SVG→PNG)
├─ cleanup_old_assets(max_age_hours=24)
└─ get_cache_stats() → dict
```

**Cache Structure:**
```
.cache/
└─ assets/
    ├─ abc123def456.png  # hashed URL → image file
    ├─ 789ghi012jkl.svg
    └─ ... (auto-cleanup after 24h)
```

---

### **4. Validation Engine** (`tools/validator.py`)

```python
DeckValidator
├─ validate_schema(spec) → errors
├─ validate_layouts(spec, template) → warnings
├─ validate_assets(spec) → warnings
│   ├─ check_image_urls()
│   └─ check_logo_path()
├─ suggest_improvements(spec) → suggestions
│   ├─ detect_content_overflow()
│   └─ recommend_layouts()
└─ generate_report() → dict
```

---

## Interaction Flow (Claude's Perspective)

**Scenario: "Create a presentation about NICE Actimize based on their website"**

```
1. Claude calls: scrape_theme("https://niceactimize.com")
   → Gets: colors, fonts, logo

2. Claude calls: list_templates()
   → Sees: default, nice-actimize templates

3. Claude generates: DeckSpec JSON (15 slides with content)

4. Claude calls: validate_deck(deck_spec)
   → Gets: warnings about image availability, layout suggestions

5. Claude refines: Adjusts spec based on warnings

6. Claude calls: generate_presentation(deck_spec)
   → Gets: file path + final warnings

7. Claude presents: Link to .pptx + summary of any issues
```

---

## Data Models (Refined)

### **ThemeSpec** (Enhanced)
```python
class ScrapedTheme(BaseModel):
    """Result from scrape_theme tool"""
    colors: ColorPalette
    fonts: FontPalette
    logo: Optional[LogoSpec] = None
    source_url: str
    warnings: List[str] = []

class ColorPalette(BaseModel):
    primary: str      # "#005596"
    secondary: str    # derived if not found
    accent: str       # derived if not found
    background: str   # "#FFFFFF"
    text: str         # "#333333"

class FontPalette(BaseModel):
    heading: str      # "Calibri Light"
    body: str         # "Calibri"
    heading_web: Optional[str] = None  # "Montserrat" (original)
    body_web: Optional[str] = None     # "Open Sans"

class LogoSpec(BaseModel):
    url: str
    cached_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
```

### **DeckSpec** (Enhanced)
```python
class DeckSpec(BaseModel):
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    footer: Optional[FooterSpec] = None
    output: OutputSpec
    theme: ThemeSpec  # Can be empty {}, scraped, direct colors, or template
    slides: List[SlideSpec]

class ThemeSpec(BaseModel):
    """Theme can be specified in multiple ways"""
    scraped: Optional[ScrapedTheme] = None
    template: Optional[str] = None  # Path to .potx
    colors: Optional[ColorPalette] = None  # Direct specification
    fonts: Optional[FontPalette] = None
    logo: Optional[LogoSpec] = None

    # If colors + fonts provided, auto-converts to ScrapedTheme
    # If empty {}, uses default Secret AI theme

class SlideSpec(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    layout: LayoutType  # TITLE, TITLE_CONTENT, SECTION, TWO_COL, CODE, etc.
    content: List[SlideContent] = []
    speaker_notes: Optional[str] = None

class LayoutType(Enum):
    TITLE = "TITLE"
    TITLE_CONTENT = "TITLE_CONTENT"
    SECTION = "SECTION"
    TWO_COL = "TWO_COL"
    IMAGE_FOCUS = "IMAGE_FOCUS"
    TABLE = "TABLE"
    CHART = "CHART"
    CODE = "CODE"  # NEW
    BLANK = "BLANK"

class ContentType(Enum):
    TEXT = "text"
    BULLETS = "bullets"
    IMAGE = "image"
    TABLE = "table"
    CHART = "chart"
    CODE = "code"  # NEW

class CodeSpec(BaseModel):
    """NEW: Code block specification"""
    code: str
    language: Optional[str] = None  # python, bash, javascript, etc.
    title: Optional[str] = None
    line_numbers: bool = False  # Future use

class SlideContent(BaseModel):
    type: ContentType
    text: Optional[str] = None
    bullets: Optional[List[str]] = None
    image: Optional[ImageSpec] = None
    table: Optional[TableSpec] = None
    chart: Optional[ChartSpec] = None
    code: Optional[Union[CodeSpec, str]] = None  # NEW
    # ... other fields
```

---

## Error Handling Strategy

### **Three Levels:**

**1. Errors (Block generation)**
- Invalid Pydantic schema
- Template file not found
- Output directory not writable

**2. Warnings (Logged, generation continues)**
- Image URL unreachable
- Layout not found (fallback used)
- Font not available (default used)

**3. Info (Returned in response)**
- Asset cached vs. downloaded
- Layouts auto-selected
- Color derived from primary

### **Response Format:**
```python
{
  "ok": true,  # False only for critical errors
  "output": "path/to/file.pptx",
  "errors": [],  # Empty if ok=true
  "warnings": ["Slide 3: image placeholder used"],
  "info": ["Generated 15 slides in 2.3s"]
}
```

---

## Playwright Integration

### **Theme Extraction Flow:**

```python
async def extract_theme(url: str) -> ScrapedTheme:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate and wait for content
        await page.goto(url, wait_until="networkidle")
        
        # Extract colors
        colors = await extract_colors_from_page(page)
        
        # Extract fonts
        fonts = await extract_fonts_from_page(page)
        
        # Extract logo
        logo = await extract_logo_from_page(page)
        
        await browser.close()
        
        return ScrapedTheme(
            colors=colors,
            fonts=fonts,
            logo=logo,
            source_url=url
        )
```

**Color Extraction:**
```python
async def extract_colors_from_page(page):
    # Try CSS variables first
    css_vars = await page.evaluate("""
        () => {
            const styles = getComputedStyle(document.documentElement);
            return {
                primary: styles.getPropertyValue('--primary-color'),
                secondary: styles.getPropertyValue('--secondary-color'),
                // ... check common variable names
            }
        }
    """)
    
    # Fallback: analyze common elements
    if not css_vars.get('primary'):
        primary = await page.evaluate("""
            () => {
                const header = document.querySelector('header, nav');
                return getComputedStyle(header).backgroundColor;
            }
        """)
    
    # Convert RGB to hex, derive secondary/accent
    return normalize_colors(css_vars)
```

---

## Testing Strategy

### **Unit Tests:**
- Color extraction from mock HTML
- Font mapping logic
- Layout fallback rules
- Graceful degradation scenarios
- **NEW:** Bullet splitting logic (colon and dash rules)
  - 24 tests covering all edge cases
  - Located in `tests/test_bullet_logic.py`

### **Integration Tests:**
- Full scrape → generate pipeline
- Invalid URL handling
- Missing asset handling
- **NEW:** Default theme application
- **NEW:** Direct color specification
- **NEW:** CODE slide rendering
- **NEW:** Code auto-splitting across slides

### **Test Files** (Located in `tests/` directory):
```
tests/
├── test_models.py              # Data model validation
├── test_server.py              # MCP server functionality
├── test_default_theme.py       # Default Secret AI theme
├── test_direct_colors.py       # Direct color specification
├── test_all_layouts.py         # All 9 layouts (including CODE)
├── test_bullet_splitting.py    # Visual bullet formatting test
├── test_bullet_logic.py        # 24 unit tests for bullet rules
├── test_code_slides.py         # CODE layout with Python/Bash
└── test_code_splitting.py      # Auto-split long code
```

### **End-to-End Tests:**
```python
def test_full_pipeline():
    # 1. Scrape theme (or use default)
    theme = scrape_theme("https://example.com")
    # OR use empty theme for default
    theme = {}

    # 2. Generate deck with CODE slides
    deck = DeckSpec(
        title="Test Deck",
        theme=theme,
        slides=[
            {
                "layout": "TITLE",
                "title": "My Presentation"
            },
            {
                "layout": "CODE",
                "title": "Python Example",
                "content": [
                    {
                        "type": "code",
                        "code": "def hello():\n    print('Hello')",
                        "language": "python"
                    }
                ]
            },
            {
                "layout": "TITLE_CONTENT",
                "title": "Key Points",
                "content": [
                    "Goal: Achieve success",  # Auto-bold prefix
                    "Result - Amazing outcome"  # Auto-bold prefix
                ]
            }
        ]
    )

    # 3. Validate
    validation = validate_deck(deck)
    assert validation["valid"] is True

    # 4. Generate
    result = generate_presentation(deck)
    assert result["ok"] is True
    assert Path(result["output"]).exists()
    assert result["slides_generated"] == 3
    assert len(result["warnings"]) == 0
```

### **Test Results (v1.1):**
- ✅ All 24 bullet logic tests passing
- ✅ Default theme correctly applied
- ✅ CODE slides render with proper formatting
- ✅ Code auto-splitting works for 50+ line scripts
- ✅ Smart bullet formatting applied to colon and dash patterns
- ✅ All layouts functional (TITLE, TITLE_CONTENT, SECTION, TWO_COL, CODE, etc.)
- ✅ Generated files valid Microsoft OOXML format

---

## Open Questions / Future Enhancements

### **Implemented in v1.1:**
- ✅ **CODE slide layout** - Display source code with proper formatting
- ✅ **Smart bullet formatting** - Auto-bold colon and dash prefixes
- ✅ **Default theme** - Secret AI branding when no theme specified
- ✅ **Code auto-splitting** - Break long code across multiple slides
- ✅ **Direct color specification** - Bypass scraping for known colors
- ✅ **Fallback extraction** - HTTP fallback when Playwright unavailable

### **Future Considerations:**

1. **Syntax Highlighting for CODE slides**
   - Integrate pygments or similar for color-coded syntax
   - Language-specific keyword highlighting
   - Custom color schemes per language

2. **Line Numbers for CODE slides**
   - Optional line numbering
   - Highlight specific line ranges
   - Support for `CodeSpec.line_numbers` flag

3. **Theme Refinement**
   - Tool: `refine_theme(theme, adjustments)` for Claude to tweak colors
   - Interactive color adjustment
   - A/B testing different color palettes

4. **Preview Generation**
   - Tool: `preview_slide(slide_spec, theme)` → PNG thumbnail
   - Quick visual validation before full generation
   - Thumbnail gallery for slide selection

5. **Batch Generation**
   - Tool: `generate_multiple(base_spec, variations)` for A/B testing
   - Generate multiple versions with different themes
   - Batch export to different formats

6. **Template Creation**
   - Tool: `create_template_from_theme(scraped_theme)` → generates .potx
   - Convert JSON theme to PowerPoint template
   - Reusable corporate branding

7. **Advanced Bullet Formatting**
   - Support for nested bullet levels
   - Custom bullet styles (numbers, letters, symbols)
   - Automatic list type detection

8. **Code Features**
   - Syntax highlighting per language
   - Code execution output display
   - Interactive code examples
   - Diff view for code changes

9. **Analytics & Insights**
   - Track which layouts are most used
   - Common validation warnings
   - Average presentation length
   - Popular color schemes

10. **Collaboration Features**
    - Version control for presentations
    - Collaborative editing
    - Comment and review system

---

## Version History

### **v1.1** (2025-01-02)
- Added CODE slide layout with auto-splitting
- Implemented smart bullet formatting (colon and dash rules)
- Added default Secret AI theme
- Enhanced theme specification (direct colors, empty theme support)
- Improved error handling with HTTP fallback
- Organized test suite in `tests/` directory
- Updated documentation (README, CHANGELOG, architecture)

### **v1.0** (Initial Release)
- Web theme extraction with Playwright
- PowerPoint generation from DeckSpec
- Theme application (colors, fonts, logos)
- Asset caching system
- Validation engine
- 5 core tools (scrape_theme, list_templates, validate_deck, generate_presentation, merge_themes)
- Support for 8 layout types
- Graceful degradation and error handling

---

