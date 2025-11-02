# Troubleshooting Guide

## Playwright Browser Issues

### Issue: "Playwright browsers not installed" or browser launch failures

If you encounter errors about Playwright browsers not being installed or browser launch failures, follow these steps:

#### 1. Install Playwright Browsers

```bash
playwright install chromium
```

This command downloads and installs the Chromium browser that Playwright uses for web scraping.

#### 2. Verify Installation

Test that Playwright is working correctly:

```bash
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); print('Playwright is working!'); browser.close(); p.stop()"
```

#### 3. Fallback Behavior

The MCP-PPTX server has built-in fallback behavior:

- **Primary Method**: Uses Playwright with full JavaScript rendering for accurate theme extraction
- **Fallback Method**: If Playwright fails, automatically falls back to simple HTTP-based extraction using BeautifulSoup

The fallback method:
- Still extracts colors, fonts, and logos from websites
- May be less accurate than Playwright-based extraction (no JavaScript execution)
- Will add warnings to the theme object indicating fallback was used

#### 4. Common Issues on macOS

If you see permission errors on macOS:

1. The server automatically adds `--no-sandbox` flag for better compatibility
2. Ensure you have sufficient disk space for browser downloads (~200MB)
3. Check that `/Users/<username>/Library/Caches/ms-playwright` directory is accessible

#### 5. Environment Variables

You can configure the following environment variables:

```bash
# Enable debug logging
export MCP_PPTX_DEBUG=1

# Set custom cache directory
export CACHE_DIR=/path/to/cache

# Set custom output directory
export OUTPUT_DIR=/path/to/output
```

## Common Errors

### Error: "object of type 'ColorPalette' has no len()"

**Cause**: This was a bug in earlier versions where the code tried to use `len()` on Pydantic model objects.

**Solution**: This has been fixed in the current version. Make sure you're using the latest code:
```bash
cd /path/to/mcp-pptx
git pull
pip install -e .
```

### Error: "Object of type HttpUrl is not JSON serializable"

**Cause**: This was a bug where Pydantic's `HttpUrl` type wasn't being properly serialized.

**Solution**: This has been fixed in the current version. The code now uses `model_dump(mode='json')` for proper serialization.

## Theme Extraction Issues

### Issue: Colors or fonts not extracted correctly

**Cause**: Website uses dynamic rendering or non-standard CSS

**Solution**:
- The fallback method will be used automatically
- You can manually specify colors in your deck specification
- Check the `warnings` field in the theme response for details

### Issue: Logo not found

**Cause**: Logo uses non-standard selectors or is dynamically loaded

**Solution**:
- Provide custom CSS selector hints:
  ```json
  {
    "url": "https://example.com",
    "selector_hints": {
      "logo": ".custom-logo-class img"
    }
  }
  ```

## Presentation Generation Issues

### Issue: File permission errors

**Cause**: Output directory not writable

**Solution**:
```bash
# Check output directory permissions
ls -la /mnt/user-data/outputs

# Or set a different output directory
export OUTPUT_DIR=~/pptx-output
mkdir -p ~/pptx-output
```

### Issue: Font not available in PowerPoint

**Cause**: Web fonts don't exist in PowerPoint

**Solution**: The server automatically maps web fonts to PowerPoint-safe alternatives. See `FONT_MAPPINGS` in `theme_extractor.py` for the full list.

## Getting Help

If you continue to experience issues:

1. Enable debug logging: `export MCP_PPTX_DEBUG=1`
2. Check the server logs for detailed error messages
3. Verify all dependencies are installed: `pip list | grep -E "playwright|pptx|mcp"`
4. Ensure you're using Python 3.9 or later: `python --version`
