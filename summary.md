
## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│          MCP Server: PowerPoint Generator               │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────┐      ┌──────────────┐                 │
│  │   Tools     │      │  Resources   │                 │
│  │             │      │              │                 │
│  │ • create_   │      │ • List       │                 │
│  │   pptx      │      │   available  │                 │
│  │ • scrape_   │      │   templates  │                 │
│  │   theme     │      │ • Theme      │                 │
│  │ • preview_  │      │   schemas    │                 │
│  │   theme     │      │              │                 │
│  └─────────────┘      └──────────────┘                 │
│                                                           │
│  ┌──────────────────────────────────────────┐           │
│  │         Core Components                   │           │
│  ├──────────────────────────────────────────┤           │
│  │ • Web Scraper (BeautifulSoup/Playwright) │           │
│  │ • Theme Extractor (colors, fonts, imgs)  │           │
│  │ • PPTX Builder (python-pptx)             │           │
│  │ • Image Processor (PIL/Pillow)           │           │
│  │ • Layout Engine (slide templates)        │           │
│  └──────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

## Core Design Components

### 1. **MCP Tools** (Functions Claude can call)

**Tool 1: `scrape_theme_from_url`**
- **Input**: URL, optional selectors/hints
- **Output**: Theme object (colors, fonts, images, layout style)
- **Purpose**: Extract visual design elements from a webpage

**Tool 2: `create_presentation`**
- **Input**: 
  - Content structure (JSON/dict with slides)
  - Theme data (from scraping or manual)
  - Options (layout preferences, image placement)
- **Output**: File path to generated .pptx
- **Purpose**: Generate the actual PowerPoint file

**Tool 3: `preview_theme`** (optional but useful)
- **Input**: Theme data
- **Output**: Sample slide preview or theme summary
- **Purpose**: Let Claude verify theme before creating full presentation

### 2. **Theme Extraction Strategy**

The scraper should extract:

```python
ThemeData = {
    "colors": {
        "primary": "#RRGGBB",
        "secondary": "#RRGGBB",
        "accent": "#RRGGBB",
        "background": "#RRGGBB",
        "text": "#RRGGBB"
    },
    "fonts": {
        "heading": "Font Name",
        "body": "Font Name"
    },
    "images": [
        {
            "url": "https://...",
            "type": "logo|hero|icon|decorative",
            "dimensions": (width, height)
        }
    ],
    "layout_style": "modern|corporate|minimal|creative",
    "spacing": {
        "margins": int,
        "line_height": float
    }
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

