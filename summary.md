# MCP-PPTX Server Summary (v1.1)

## High-Level Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│            MCP Server: PowerPoint Generator v1.1                  │
├───────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────┐      ┌────────────────────────┐             │
│  │   MCP Tools     │      │  Resources             │             │
│  │                 │      │                        │             │
│  │ • scrape_theme  │      │ • Default Secret AI    │             │
│  │ • list_templates│      │   theme (Red/Cyan)     │             │
│  │ • validate_deck │      │ • PowerPoint templates │             │
│  │ • generate_     │      │ • Theme schemas        │             │
│  │   presentation  │      │ • Layout definitions   │             │
│  │ • merge_themes  │      │                        │             │
│  └─────────────────┘      └────────────────────────┘             │
│                                                                     │
│  ┌───────────────────────────────────────────────────┐            │
│  │         Core Components                            │            │
│  ├───────────────────────────────────────────────────┤            │
│  │ • Web Scraper (Playwright + HTTP fallback)        │            │
│  │ • Theme Extractor (colors, fonts, logos)          │            │
│  │ • Default Theme Loader (Secret AI branding)       │            │
│  │ • PPTX Builder (python-pptx)                      │            │
│  │ • Smart Bullet Formatter (colon & dash rules)     │            │
│  │ • CODE Slide Renderer (monospace + auto-split)    │            │
│  │ • Layout Engine (9 layouts + theme applicator)    │            │
│  │ • Asset Cache (24-hour TTL)                       │            │
│  └───────────────────────────────────────────────────┘            │
└───────────────────────────────────────────────────────────────────┘
```

## Core Design Components

### 1. **MCP Tools** (Functions Claude can call)

**Tool 1: `scrape_theme`**
- **Input**: URL, optional selectors, max images
- **Output**: Theme object (colors, fonts, logos, images)
- **Purpose**: Extract visual design elements from any webpage
- **Implementation**: Playwright with HTTP fallback

**Tool 2: `generate_presentation`**
- **Input**: DeckSpec (content structure, theme, slides, output config)
- **Output**: File path to generated .pptx and generation stats
- **Purpose**: Generate PowerPoint from comprehensive deck specification
- **Features**: 9 layouts, smart bullet formatting, CODE slides, auto-splitting

**Tool 3: `list_templates`**
- **Input**: None
- **Output**: Available theme templates and their metadata
- **Purpose**: List pre-configured themes (including default Secret AI theme)

**Tool 4: `validate_deck_spec`**
- **Input**: DeckSpec JSON
- **Output**: Validation results with detailed error messages
- **Purpose**: Validate deck specification before generation

**Tool 5: `merge_themes`**
- **Input**: Base theme, override theme
- **Output**: Merged theme object
- **Purpose**: Combine multiple theme sources with intelligent merging

### 2. **Theme System**

**Default Theme (Secret AI Branding)**:
```python
default_theme = {
    "colors": {
        "primary": "#E3342F",      # Red
        "secondary": "#FFE9D3",    # Light Peach
        "accent": "#1CCBD0",       # Cyan
        "background": "#FFFFFF",   # White
        "text": "#000000"          # Black
    },
    "fonts": {
        "heading": "Arial",
        "body": "Arial"
    },
    "logo": "default_logo.png"  # Optional Secret AI logo
}
```

**Theme Specification Options**:

1. **Default Theme**: Empty theme object `{}` uses Secret AI branding
2. **Scraped Theme**: Use `scrape_theme` tool to extract from URL
3. **Direct Colors**: Specify colors directly in DeckSpec
4. **Merged Theme**: Use `merge_themes` to combine sources

**Scraped Theme Structure**:
```python
ScrapedTheme = {
    "colors": {
        "primary": "#RRGGBB",
        "secondary": "#RRGGBB",
        "accent": "#RRGGBB",
        "background": "#FFFFFF",
        "text": "#000000"
    },
    "fonts": {
        "heading": "Font Name",
        "body": "Font Name"
    },
    "images": [
        {
            "url": "https://...",
            "type": "logo|background",
            "alt_text": "Description"
        }
    ]
}
```

### 3. **Content Structure**

Standard format for presentation content:

```python
PresentationContent = {
    "title": "Presentation Title",
    "slides": [
        {
            "type": "title_slide",
            "title": "Main Title",
            "subtitle": "Subtitle"
        },
        {
            "type": "content_slide",
            "title": "Slide Title",
            "content": [
                {"type": "text", "text": "Bullet point"},
                {"type": "image", "url": "...", "caption": "..."}
            ],
            "layout": "single_column|two_column|image_left|image_right"
        },
        {
            "type": "section_header",
            "title": "Section Name"
        }
    ]
}
```

### 4. **Key Technical Decisions**

**Web Scraping Approach:**
- **Option A**: BeautifulSoup + requests (lightweight, fast, limited JS support)
- **Option B**: Playwright (handles JS-heavy sites, slower, more dependencies)
- **Recommendation**: Start with BeautifulSoup, add Playwright as optional dependency

**Color Extraction:**
- Use CSS parsing for declared colors
- Analyze images for dominant colors (using PIL/colorthief)
- Build a color palette ranked by usage frequency

**Image Handling:**
- Download and cache images locally
- Resize/optimize for PowerPoint (avoid huge file sizes)
- Respect image licenses (maybe add metadata tracking)

**Font Mapping:**
- Scrape CSS font-family declarations
- Map web fonts to PowerPoint-available fonts (fallback strategy)
- Store common web→PowerPoint font mappings

### 5. **Error Handling & Edge Cases**

- **Scraping failures**: Graceful degradation to default theme
- **Missing images**: Placeholder or skip
- **Rate limiting**: Respect robots.txt, add delays
- **Large presentations**: Streaming/chunked generation
- **Invalid URLs**: Validation before scraping

### 6. **File Management**

```
Output Structure:
/outputs/
  ├── presentation_[timestamp].pptx
  ├── themes/
  │   └── [url_hash].json (cached themes)
  └── assets/
      └── [url_hash]/ (downloaded images)
```

## Proposed API Design

```python
# Tool 1: Scrape Theme
{
    "name": "scrape_theme_from_url",
    "description": "Extract visual theme from a webpage",
    "parameters": {
        "url": "https://example.com",
        "extract_images": true,
        "max_images": 10
    }
}

# Tool 2: Create Presentation
{
    "name": "create_presentation",
    "description": "Generate PowerPoint from content and theme",
    "parameters": {
        "content": {/* PresentationContent structure */},
        "theme": {/* ThemeData or url to scrape */},
        "output_name": "my_presentation"
    }
}
```

## Questions to Consider

1. **Should we support multiple theme sources?** (e.g., combine themes from multiple URLs)
2. **Do we want template presets?** (e.g., "corporate", "creative", "minimal")
3. **Should the server validate content before generation?** (check for missing data)
4. **Do we need slide transition/animation support?**
5. **Should we cache scraped themes?** (for repeated use)

