Perfect! Those are excellent choices. Let me design a detailed architecture based on your preferences.

---

# MCP-PPTX Server Architecture v1.0

## Design Philosophy

**Core Principles:**
1. **Composable Tools** - Claude orchestrates multiple focused tools
2. **Lightweight Theme Extraction** - Colors, fonts, logo only
3. **Claude as Content Creator** - Server is a rendering engine
4. **Modern Web Support** - Playwright for JS-heavy sites
5. **Minimal Caching** - Only downloaded assets
6. **Graceful Degradation** - Always produce output + warnings

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
        "name": "default",
        "path": "themes/default.potx",
        "layouts": ["TITLE", "TITLE_CONTENT", "TWO_COL", "IMAGE_FOCUS"],
        "preview": "themes/default_preview.png"  # optional
      },
      {
        "name": "nice-actimize",
        "path": "themes/nice-actimize.potx",
        "layouts": ["TITLE", "SECTION", "TITLE_CONTENT", "TWO_COL", "TABLE", "CHART"]
      }
    ]
  }
```

**Purpose:** Let Claude see available templates and their capabilities.

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
├─ renderer.py (orchestration)
├─ layouts.py (layout resolution + fallbacks)
├─ theme_applicator.py (apply colors, fonts, logos)
├─ content_fillers.py
│   ├─ _fill_title()
│   ├─ _fill_bullets()
│   ├─ _fill_images()
│   ├─ _fill_table()
│   └─ _fill_chart()
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

### **DeckSpec** (Unchanged but referenced)
```python
class DeckSpec(BaseModel):
    title: str
    output: OutputSpec
    theme: ThemeSpec  # Can reference a .potx OR embed ScrapedTheme
    slides: List[SlideSpec]
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

### **Integration Tests:**
- Full scrape → generate pipeline
- Invalid URL handling
- Missing asset handling

### **End-to-End Tests:**
```python
def test_full_pipeline():
    # 1. Scrape theme
    theme = scrape_theme("https://example.com")
    assert theme.colors.primary is not None
    
    # 2. Generate deck
    deck = DeckSpec(
        title="Test Deck",
        theme={"scraped": theme, "template": "themes/default.potx"},
        slides=[...]
    )
    
    # 3. Validate
    validation = validate_deck(deck)
    assert validation["valid"] is True
    
    # 4. Generate
    result = generate_presentation(deck)
    assert result["ok"] is True
    assert Path(result["output"]).exists()
```

---

## Open Questions / Future Enhancements

1. **Should we support theme refinement?**
   - Tool: `refine_theme(theme, adjustments)` for Claude to tweak colors

2. **Preview generation?**
   - Tool: `preview_slide(slide_spec, theme)` → PNG thumbnail

3. **Batch generation?**
   - Tool: `generate_multiple(base_spec, variations)` for A/B testing

4. **Template creation?**
   - Tool: `create_template_from_theme(scraped_theme)` → generates .potx

5. **Analytics?**
   - Track which layouts are most used, common validation warnings

---

