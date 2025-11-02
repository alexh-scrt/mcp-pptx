# MCP-PPTX Server

An MCP (Model Context Protocol) server for generating PowerPoint presentations with automated web theme extraction.

## Features

- **Web Theme Extraction**: Automatically extract colors, fonts, and logos from websites using Playwright
- **PowerPoint Generation**: Create professional presentations from structured specifications
- **Theme Application**: Apply extracted themes to presentations automatically
- **Code Slides**: Dedicated layout for displaying source code with syntax-appropriate formatting
- **Smart Bullet Formatting**: Automatic bold formatting for prefixed bullet points (colon and dash rules)
- **Asset Caching**: Efficient caching of downloaded images and resources
- **Validation**: Comprehensive validation of deck specifications before generation
- **Graceful Degradation**: Robust error handling with fallbacks
- **Default Theme**: Secret AI default theme (Red, Cyan, White) when no theme specified

## Architecture

The server implements 5 main tools as described in the architecture:

1. **`scrape_theme`** - Extract theme elements from websites
2. **`list_templates`** - List available PowerPoint templates
3. **`validate_deck`** - Validate deck specifications
4. **`generate_presentation`** - Generate PowerPoint files
5. **`merge_themes`** - Combine multiple scraped themes

## Installation

### Prerequisites

- Python 3.8+
- Conda (recommended) or virtualenv

### Setup with Conda (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd mcp-pptx

# Create conda environment
conda create -n mcp-pptx python=3.11
conda activate mcp-pptx

# Install package in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### Setup with pip/virtualenv

```bash
# Clone the repository
git clone <repository-url>
cd mcp-pptx

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in development mode
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Usage

### Claude Desktop Configuration

Configure the MCP server in Claude Desktop by editing:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "MCP PPTX": {
      "command": "/Users/ki11erc0der/miniconda/envs/mcp-pptx/bin/python",
      "args": ["/Users/ki11erc0der/Workspace/mcp-pptx/run_server.py"],
      "env": {
        "MCP_PPTX_OUTPUT_DIR": "/Users/ki11erc0der/pptx-output"
      }
    }
  }
}
```

**Note**: Adjust paths to match your system:
- Replace `/Users/ki11erc0der/miniconda/envs/mcp-pptx/bin/python` with your Python path
- Replace `/Users/ki11erc0der/Workspace/mcp-pptx/run_server.py` with your server script path
- Set `MCP_PPTX_OUTPUT_DIR` to your desired output directory

To find your Python path in the conda environment:
```bash
conda activate mcp-pptx
which python  # macOS/Linux
where python  # Windows
```

### Viewing Logs

Monitor MCP server logs in real-time:

**macOS**:
```bash
tail -f ~/Library/Logs/Claude/mcp-server-MCP\ PPTX.log
```

**Windows**:
```powershell
Get-Content "$env:APPDATA\Claude\Logs\mcp-server-MCP PPTX.log" -Wait
```

### As Standalone MCP Server

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

## Quick Start

1. Install and activate environment:
   ```bash
   conda activate mcp-pptx
   pip install -e .
   ```

2. Configure Claude Desktop (see Configuration section above)

3. Restart Claude Desktop

4. Create a presentation:
   ```
   Create a 5-slide presentation about Python basics with:
   - Title slide
   - Introduction with bullet points
   - A code example showing a simple function
   - Best practices section
   - Thank you slide

   Use the default theme.
   ```

## Example Usage with Claude

### Basic Presentation
```
Create a 10-slide presentation about NICE Actimize using their website theme
```

### With Web Scraping
```
1. Scrape the theme from https://example.com
2. Create a presentation about the company using the scraped theme
```

### With Code Examples
```
Create a Python tutorial presentation with:
- Title slide introducing Python
- 3 code slides showing:
  * Basic syntax
  * Functions and loops
  * File handling
- Summary slide

Use CODE layout for all code examples and split long code across multiple slides.
```

### With Smart Bullet Formatting
```
Create a presentation about project phases with these bullets:
- Phase 1: Planning and requirements gathering
- Phase 2: Design and architecture
- Implementation - Building the core features
- Testing - Quality assurance and bug fixes
- Deployment - Production release
```

### With Direct Theme Colors
```
Create a 5-slide presentation using these colors:
- Primary: #E3342F (red)
- Accent: #1CCBD0 (cyan)
- Background: white

Include title slide, 3 content slides, and closing slide.
```

## Configuration

### Environment Variables

- `MCP_PPTX_OUTPUT_DIR` or `OUTPUT_DIR`: Default output directory (default: `~/pptx-output`)
- `CACHE_DIR`: Directory for asset cache (default: `~/.cache/mcp-pptx/assets`)
- `MAX_CACHE_AGE_HOURS`: Cache expiration time (default: 24 hours)
- `MCP_PPTX_DEBUG`: Enable debug logging (set to `1` or `true`)

Example configuration in Claude Desktop:
```json
{
  "mcpServers": {
    "MCP PPTX": {
      "command": "/path/to/python",
      "args": ["/path/to/run_server.py"],
      "env": {
        "MCP_PPTX_OUTPUT_DIR": "/Users/username/pptx-output",
        "MCP_PPTX_DEBUG": "1"
      }
    }
  }
}
```

### Template and Theme Directory

- **Templates**: Place PowerPoint templates (.potx files) in the `themes/` directory
- **Default Theme**: The server includes a default Secret AI theme (`themes/default_theme.json`) with:
  - Primary color: Red (#E3342F)
  - Secondary color: Light Peach (#FFE9D3)
  - Accent color: Cyan (#1CCBD0)
  - Background: White (#FFFFFF)
  - Text: Dark Gray (#111827)

## Data Models

### DeckSpec
Complete specification for a presentation including:
- Title, subtitle, author
- Theme specification:
  - Option 1: Scraped theme from website (use `scrape_theme` tool first)
  - Option 2: Template file path (`.potx` file)
  - Option 3: Direct colors and fonts (simplified format)
- Slide specifications with layouts and content
- Output preferences

Example using direct colors/fonts:
```json
{
  "title": "My Presentation",
  "theme": {
    "colors": {
      "primary": "#E3342F",
      "secondary": "#1CCBD0",
      "accent": "#FFE9D3",
      "background": "#FFFFFF",
      "text": "#111827"
    },
    "fonts": {
      "heading": "Calibri",
      "body": "Arial"
    }
  },
  "slides": [...]
}
```

### ScrapedTheme
Result of web theme extraction:
- Color palette (primary, secondary, accent, background, text)
- Font palette (heading, body fonts)
- Logo specification with cached assets
- Source URL and extraction warnings

## Supported Layouts

- `TITLE` - Title slide with red background
- `TITLE_CONTENT` - Title with content area (white background with red title bar)
- `SECTION` - Section divider with rotating colors (Cyan → Red → Peach)
- `TWO_COL` - Two column layout for side-by-side content
- `CODE` - Code slide with monospace font and light gray background
- `IMAGE_FOCUS` - Image-focused layout
- `TABLE` - Table layout
- `CHART` - Chart layout
- `BLANK` - Blank slide

### Layout Examples

**CODE Layout** - For displaying source code:
```json
{
  "layout": "CODE",
  "title": "Python Example",
  "content": [
    {
      "type": "code",
      "code": "def hello():\n    print('Hello, World!')",
      "language": "python"
    }
  ]
}
```

Features:
- Font: Courier New, 20pt
- Code box background: Light gray (#F5F5F5)
- Slide background: White
- Preserves indentation and formatting
- Auto-splits long code (>15 lines) across multiple slides

## Supported Content Types

- **Text content** - Plain text or paragraphs
- **Bullet points** - With smart formatting (see below)
- **Images** - With URL, alt text, captions
- **Tables** - Headers and data rows
- **Charts** - Various types with data
- **Code** - Source code with syntax formatting

### Smart Bullet Formatting

Bullets are automatically formatted with bold prefixes using two rules:

**Colon Rule**: 1-4 words followed by `:` → Bold
```
"Goal: Achieve success" → "Goal:" is bold
"Key Point: Important info" → "Key Point:" is bold
```

**Dash Rule**: 1-4 words followed by ` - ` → Bold
```
"Goal - Achieve success" → "Goal -" is bold
"Important Note - Details here" → "Important Note -" is bold
```

**Precedence**: Colon rule is checked first, then dash rule

## Error Handling

The server implements three levels of error handling:

1. **Errors** - Block generation (invalid schema, missing files)
2. **Warnings** - Logged, generation continues (missing images, layout fallbacks)
3. **Info** - Returned in response (asset status, auto-selections)

## Development

### Running Tests

The project includes several test scripts in the `tests/` directory:

```bash
# Test default theme application
python tests/test_default_theme.py

# Test bullet splitting rules (colon and dash)
python tests/test_bullet_splitting.py

# Test CODE slide layout
python tests/test_code_slides.py

# Test code splitting across multiple slides
python tests/test_code_splitting.py

# Test all layouts
python tests/test_all_layouts.py

# Test bullet logic unit tests
python tests/test_bullet_logic.py

# Test direct color specification
python tests/test_direct_colors.py

# Run all tests with pytest (if available)
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

### Debugging

Enable debug logging:
```bash
export MCP_PPTX_DEBUG=1  # macOS/Linux
set MCP_PPTX_DEBUG=1     # Windows
```

Then monitor logs:
```bash
tail -f ~/Library/Logs/Claude/mcp-server-MCP\ PPTX.log  # macOS
```

## Troubleshooting

### Server Not Appearing in Claude Desktop

1. Verify configuration file location:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Check Python path:
   ```bash
   conda activate mcp-pptx
   which python  # Should match path in config
   ```

3. Verify server script exists:
   ```bash
   ls -la /path/to/run_server.py
   ```

4. Check logs for errors:
   ```bash
   tail -50 ~/Library/Logs/Claude/mcp-server-MCP\ PPTX.log
   ```

### Import Errors

If you see import errors, ensure the package is installed correctly:
```bash
conda activate mcp-pptx
cd /path/to/mcp-pptx
pip install -e .
```

### Playwright Issues

If web scraping fails:
```bash
conda activate mcp-pptx
playwright install chromium
```

### Output Directory Issues

Ensure the output directory exists and is writable:
```bash
mkdir -p ~/pptx-output
chmod 755 ~/pptx-output
```

## Testing

Test files are located in the `tests/` directory:

- `tests/test_default_theme.py` - Tests default Secret AI theme application
- `tests/test_direct_colors.py` - Tests direct color specification
- `tests/test_all_layouts.py` - Tests all slide layouts
- `tests/test_bullet_splitting.py` - Tests bullet formatting rules
- `tests/test_code_slides.py` - Tests CODE layout functionality
- `tests/test_code_splitting.py` - Tests automatic code splitting
- `tests/test_bullet_logic.py` - Unit tests for bullet splitting logic
- `tests/test_models.py` - Unit tests for data models
- `tests/test_server.py` - Unit tests for MCP server

All tests create output in `~/pptx-output/` directory.

Run all tests:
```bash
# Run individual tests
python tests/test_code_slides.py

# Run all tests with pytest
pytest tests/
```

## License

MIT License
