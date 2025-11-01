# MCP-PPTX Server

An MCP (Model Context Protocol) server for generating PowerPoint presentations with automated web theme extraction.

## Features

- **Web Theme Extraction**: Automatically extract colors, fonts, and logos from websites using Playwright
- **PowerPoint Generation**: Create professional presentations from structured specifications
- **Theme Application**: Apply extracted themes to presentations automatically
- **Asset Caching**: Efficient caching of downloaded images and resources
- **Validation**: Comprehensive validation of deck specifications before generation
- **Graceful Degradation**: Robust error handling with fallbacks

## Architecture

The server implements 5 main tools as described in the architecture:

1. **`scrape_theme`** - Extract theme elements from websites
2. **`list_templates`** - List available PowerPoint templates
3. **`validate_deck`** - Validate deck specifications
4. **`generate_presentation`** - Generate PowerPoint files
5. **`merge_themes`** - Combine multiple scraped themes

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-pptx

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Usage

### As MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "mcp-pptx": {
      "command": "python",
      "args": ["-m", "mcp_pptx"]
    }
  }
}
```

### Direct Usage

```python
from mcp_pptx.server import MCPPPTXServer

server = MCPPPTXServer()
await server.run()
```

## Example Usage with Claude

1. **Extract theme from website**:
   ```
   Please scrape the theme from https://niceactimize.com
   ```

2. **Generate presentation**:
   ```
   Create a 10-slide presentation about NICE Actimize using their website theme
   ```

## Configuration

### Environment Variables

- `CACHE_DIR`: Directory for asset cache (default: `.cache/assets`)
- `OUTPUT_DIR`: Default output directory (default: `/mnt/user-data/outputs`)
- `MAX_CACHE_AGE_HOURS`: Cache expiration time (default: 24)

### Template Directory

Place PowerPoint templates (.potx files) in the `themes/` directory.

## Data Models

### DeckSpec
Complete specification for a presentation including:
- Title, subtitle, author
- Theme specification (scraped or template)
- Slide specifications with layouts and content
- Output preferences

### ScrapedTheme
Result of web theme extraction:
- Color palette (primary, secondary, accent, background, text)
- Font palette (heading, body fonts)
- Logo specification with cached assets
- Source URL and extraction warnings

## Supported Layouts

- `TITLE` - Title slide
- `TITLE_CONTENT` - Title and content
- `SECTION` - Section header
- `TWO_COL` - Two column layout
- `IMAGE_FOCUS` - Image-focused layout
- `TABLE` - Table layout
- `CHART` - Chart layout
- `BLANK` - Blank slide

## Supported Content Types

- Text content
- Bullet points
- Images (with URL, alt text, captions)
- Tables (headers and data rows)
- Charts (various types with data)

## Error Handling

The server implements three levels of error handling:

1. **Errors** - Block generation (invalid schema, missing files)
2. **Warnings** - Logged, generation continues (missing images, layout fallbacks)
3. **Info** - Returned in response (asset status, auto-selections)

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black src/
isort src/
```

### Type Checking

```bash
mypy src/
```

## License

MIT License
