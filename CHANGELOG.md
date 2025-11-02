# Changelog

## [Unreleased] - 2025-01-02

### Added

#### CODE Slide Layout
- New `CODE` layout type for displaying source code
- Automatic code formatting with Courier New font (20pt)
- Light gray background (#F5F5F5) for code blocks
- Support for optional title and language metadata
- Automatic code splitting across multiple slides (>15 lines per slide)
- Preserved indentation and formatting

#### Smart Bullet Formatting
- **Colon Rule**: Automatically bolds 1-4 words followed by `:`
  - Example: "Goal: Achieve success" → **Goal:** Achieve success
- **Dash Rule**: Automatically bolds 1-4 words followed by ` - `
  - Example: "Goal - Achieve success" → **Goal -** Achieve success
- Rules applied exclusively with colon taking precedence

#### Default Theme
- Added Secret AI default theme (`themes/default_theme.json`)
- Automatically applied when theme is empty or not specified
- Colors: Red (#E3342F), Cyan (#1CCBD0), Peach (#FFE9D3)
- Fonts: Calibri (heading), Tahoma (body)

#### Documentation
- Comprehensive README.md update (473 lines)
- Installation instructions with conda environment setup
- Claude Desktop configuration with exact paths
- Log viewing instructions for debugging
- Troubleshooting section with common issues
- Quick start guide
- Multiple usage examples

### Changed
- Updated `LayoutType` enum to include `CODE`
- Updated `ContentType` enum to include `code`
- Enhanced `SlideContent` model with `code` field
- Improved renderer to handle CODE slides with white background
- Updated server.py tool descriptions to include CODE layout
- Modified content_fillers.py font size from 24pt to 20pt for better fit
- Updated server.py max lines from 25 to 15 for better readability

### Fixed
- Fixed TWO_COL layout slide dimension access (now uses standard 10" x 7.5")
- Fixed code box background color application
- Improved error handling in code rendering

### Testing
- Added `tests/test_code_slides.py` - Tests CODE layout with Python and Bash examples
- Added `tests/test_code_splitting.py` - Tests automatic code splitting across slides
- Added `tests/test_bullet_splitting.py` - Tests bullet formatting with visual examples
- Added `tests/test_bullet_logic.py` - Unit tests for colon and dash rules (24 tests, all passing)
- Added `tests/test_default_theme.py` - Tests default theme application
- Added `tests/test_direct_colors.py` - Tests direct color specification
- Added `tests/test_all_layouts.py` - Comprehensive test of all 10 layouts

All test files organized in `tests/` directory.
All tests passing with output files generated successfully in `~/pptx-output/`.

## Files Modified

### Core Implementation
- `src/mcp_pptx/models/deck_spec.py` - Added CODE layout and content types, CodeSpec model
- `src/mcp_pptx/rendering/content_fillers.py` - Added code rendering and splitting logic
- `src/mcp_pptx/rendering/theme_applicator.py` - Added CODE background handling
- `src/mcp_pptx/rendering/renderer.py` - Integrated CODE slide rendering
- `src/mcp_pptx/server.py` - Updated tool descriptions and schemas

### Documentation
- `README.md` - Complete rewrite with 490 lines
- `CHANGELOG.md` - Created this changelog

### Testing
- 7 new test scripts created and organized in `tests/` directory
- All tests create output in `~/pptx-output/`

## Installation Notes

### Conda Environment Setup
```bash
conda create -n mcp-pptx python=3.11
conda activate mcp-pptx
pip install -e .
playwright install chromium
```

### Claude Desktop Configuration
Location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

```json
{
  "mcpServers": {
    "MCP PPTX": {
      "command": "/Users/username/miniconda/envs/mcp-pptx/bin/python",
      "args": ["/Users/username/Workspace/mcp-pptx/run_server.py"],
      "env": {
        "MCP_PPTX_OUTPUT_DIR": "/Users/username/pptx-output"
      }
    }
  }
}
```

### Viewing Logs
```bash
tail -f ~/Library/Logs/Claude/mcp-server-MCP\ PPTX.log
```

## Statistics

- **Lines Added**: ~500 lines of new code
- **New Features**: 3 major features (CODE slides, bullet formatting, default theme)
- **Tests Created**: 7 comprehensive test scripts
- **Documentation**: 473-line README with complete setup guide
- **Test Coverage**: All layouts and features tested successfully
