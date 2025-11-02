"""MCP-PPTX Server implementation."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import ServerCapabilities
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from .extraction.theme_extractor import ThemeExtractor
from .models.deck_spec import DeckSpec, ValidationResult
from .models.theme_spec import ScrapedTheme
from .rendering.renderer import PresentationRenderer
from .tools.validator import DeckValidator
from .cache.asset_cache import AssetCache

logger = logging.getLogger(__name__)


class MCPPPTXServer:
    """MCP server for PowerPoint presentation generation."""

    def __init__(self) -> None:
        logger.info("Initializing MCP-PPTX Server...")
        self.server = Server("mcp-pptx")
        logger.info("Created MCP server instance")
        
        self.theme_extractor = ThemeExtractor()
        logger.info("Initialized ThemeExtractor")
        
        self.renderer = PresentationRenderer()
        logger.info("Initialized PresentationRenderer")
        
        self.validator = DeckValidator()
        logger.info("Initialized DeckValidator")
        
        self.asset_cache = AssetCache()
        logger.info("Initialized AssetCache")
        
        self._setup_handlers()
        logger.info("MCP-PPTX Server initialization complete")

    def _setup_handlers(self) -> None:
        """Set up MCP server handlers."""
        logger.info("Setting up MCP server handlers...")

        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools."""
            logger.info("Received list_tools request")
            tools_result = ListToolsResult(
                tools=[
                    Tool(
                        name="scrape_theme",
                        description="Extract theme elements (colors, fonts, logo) from a website",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL of the website to extract theme from"
                                },
                                "extract_logo": {
                                    "type": "boolean",
                                    "default": True,
                                    "description": "Whether to extract and cache the logo"
                                },
                                "selector_hints": {
                                    "type": "object",
                                    "description": "Optional CSS selector hints for logo extraction",
                                    "properties": {
                                        "logo": {"type": "string"}
                                    }
                                }
                            },
                            "required": ["url"]
                        }
                    ),
                    Tool(
                        name="list_templates",
                        description="List available PowerPoint templates",
                        inputSchema={
                            "type": "object",
                            "properties": {}
                        }
                    ),
                    Tool(
                        name="validate_deck",
                        description="Validate a deck specification before generation",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "deck_spec": {
                                    "type": "object",
                                    "description": "The deck specification to validate"
                                }
                            },
                            "required": ["deck_spec"]
                        }
                    ),
                    Tool(
                        name="generate_presentation",
                        description="""Generate a PowerPoint presentation from a deck specification.

FLEXIBLE INPUT: This tool is very accommodating with input formats:
- Layout names: Use UPPERCASE (TITLE, TITLE_CONTENT, SECTION) or lowercase (title, title_content)
- Content: Can be plain strings, dicts with 'items'/'bullets', or full content objects
- Theme: Can use scraped theme, direct colors/fonts, or template path

LAYOUTS AVAILABLE:
- TITLE: Title slide with large title and subtitle
- TITLE_CONTENT: Title with content area (most common)
- SECTION: Section divider slide
- TWO_COL: Two column layout
- CODE: Code slide with monospace font and light gray background
- BLANK: Blank slide

CONTENT FORMATS (all supported):
1. Simple strings: content: ["Bullet 1", "Bullet 2"]
2. Dict with items: content: {"type": "bullets", "items": ["Item 1", "Item 2"]}
3. Full objects: content: [{"type": "text", "text": "Content here"}]
4. Code format: content: [{"type": "code", "code": "print('hello')"}]

CODE SLIDES (layout: CODE):
- Use for displaying source code, scripts, or command-line examples
- Automatically formatted with:
  * Courier New font, 20pt
  * Light gray background (#F5F5F5) for code box
  * White slide background
  * Preserves indentation and formatting
- Content options:
  1. Simple string: content: [{"type": "code", "code": "your code here"}]
  2. With metadata: content: [{"type": "code", "code": "code text", "language": "python", "title": "Example Script"}]
- IMPORTANT: If code is too long (>15 lines), split it across multiple CODE slides
- Each CODE slide should contain ONLY code - no mixed content
- Examples:
  * Python script
  * Bash commands
  * Configuration files
  * API examples

THEME OPTIONS:
1. Default: Use empty theme object {} to apply Secret AI default theme (Red, Cyan, White)
2. Scraped: Use output from scrape_theme tool
3. Direct: Provide colors and fonts directly
4. Template: Path to .potx file

NOTE: If theme is empty {}, the default Secret AI theme will be automatically applied.

RECOMMENDED PRESENTATION STRUCTURE (unless user specifies otherwise):

1. TITLE SLIDE (layout: TITLE)
   - Presentation title and subtitle/tagline
   - Optionally include visual or brand mark

2. AGENDA/OUTLINE (layout: TITLE_CONTENT)
   - High-level bullets of what will be covered (3-5 items)
   - Helps audience set expectations
   - Title: "Agenda" or "What We'll Cover"

3. INTRODUCTION/CONTEXT (layout: TITLE_CONTENT)
   - Why this topic matters
   - Key problem or opportunity being addressed
   - Optionally include hook or compelling statistic
   - Title: "Introduction" or "Why This Matters"

4. SECTION 1: KEY POINT/THEME A (layout: SECTION for section divider)
   - Section divider introducing first major theme
   - Then sequence of content slides:
     * Bullet slide with key points (TITLE_CONTENT)
     * Visual/diagram slide (IMAGE_FOCUS or TITLE_CONTENT)
     * Data/chart slide (CHART or TITLE_CONTENT)
     * Summary/table slide (TABLE or TITLE_CONTENT)
   - Optional transition slide: "What This Means" or "Key Takeaway"

5. SECTION 2: KEY POINT/THEME B (layout: SECTION for section divider)
   - Follow same pattern: bullet → visual → chart → summary
   - Maintain consistent visual style
   - Emphasize insights, not just raw data
   - End with implications slide

6. SECTION 3: KEY POINT/THEME C (layout: SECTION for section divider)
   - Repeat pattern for third major theme
   - Conclude with implications or next steps
   - Keep consistent with previous sections

7. SYNTHESIS/CONCLUSIONS (layout: TITLE_CONTENT)
   - Wrap all major themes together
   - Overall insight or recommendation
   - 3-5 key takeaways as bullets
   - Title: "Conclusions" or "Key Takeaways"

8. Q&A SLIDE (layout: TITLE_CONTENT or BLANK)
   - Invite questions
   - Optionally include contact details
   - Title: "Questions?" or "Q&A"

9. THANK YOU/APPENDIX (layout: TITLE or BLANK)
   - Thank you slide with contact info
   - Or appendix marker for backup slides

BEST PRACTICES:
- Use SECTION layout to clearly separate major themes
- Group related content: concept → visual → data → insight
- Include transition/summary slides between sections
- Balance text-heavy and visual slides
- End sections with "So what?" or implication slides
- Keep consistent structure across sections""",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "deck_spec": {
                                    "type": "object",
                                    "description": "Complete presentation specification",
                                    "properties": {
                                        "title": {
                                            "type": "string",
                                            "description": "Presentation title"
                                        },
                                        "subtitle": {
                                            "type": "string",
                                            "description": "Optional presentation subtitle"
                                        },
                                        "theme": {
                                            "type": "object",
                                            "description": "Theme specification - can include colors, fonts, logo, or scraped theme",
                                            "properties": {
                                                "colors": {
                                                    "type": "object",
                                                    "description": "Color palette with primary, secondary, accent, background, text (hex values)"
                                                },
                                                "fonts": {
                                                    "type": "object",
                                                    "description": "Font palette with heading and body font names"
                                                },
                                                "logo": {
                                                    "type": "object",
                                                    "description": "Optional logo with path or url"
                                                },
                                                "scraped": {
                                                    "type": "object",
                                                    "description": "Output from scrape_theme tool"
                                                }
                                            }
                                        },
                                        "slides": {
                                            "type": "array",
                                            "description": "Array of slide specifications",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "layout": {
                                                        "type": "string",
                                                        "description": "Layout type (TITLE, TITLE_CONTENT, SECTION, CODE, etc.) - case insensitive",
                                                        "enum": ["TITLE", "TITLE_CONTENT", "SECTION", "TWO_COL", "IMAGE_FOCUS", "TABLE", "CHART", "CODE", "BLANK"]
                                                    },
                                                    "title": {
                                                        "type": "string",
                                                        "description": "Slide title"
                                                    },
                                                    "subtitle": {
                                                        "type": "string",
                                                        "description": "Slide subtitle (for TITLE layout)"
                                                    },
                                                    "content": {
                                                        "description": "Slide content - can be array of strings, objects, or single object",
                                                        "oneOf": [
                                                            {
                                                                "type": "array",
                                                                "items": {"type": "string"},
                                                                "description": "Array of content strings (each becomes a bullet or text line)"
                                                            },
                                                            {
                                                                "type": "array",
                                                                "items": {"type": "object"},
                                                                "description": "Array of content objects with type and content"
                                                            },
                                                            {
                                                                "type": "object",
                                                                "description": "Single content object"
                                                            }
                                                        ]
                                                    }
                                                },
                                                "required": ["layout"]
                                            }
                                        }
                                    },
                                    "required": ["title", "theme", "slides"]
                                }
                            },
                            "required": ["deck_spec"]
                        }
                    ),
                    Tool(
                        name="merge_themes",
                        description="Merge multiple scraped themes into one",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "themes": {
                                    "type": "array",
                                    "items": {"type": "object"},
                                    "description": "List of theme specifications to merge"
                                },
                                "priority": {
                                    "type": "string",
                                    "enum": ["first", "balanced"],
                                    "default": "balanced",
                                    "description": "Merge strategy"
                                }
                            },
                            "required": ["themes"]
                        }
                    )
                ]
            )
            logger.info(f"Returning {len(tools_result.tools)} available tools")
            return tools_result

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]]
        ) -> CallToolResult:
            """Handle tool calls."""
            logger.info(f"Received tool call: {name}")
            logger.debug(f"Tool arguments: {arguments}")
            try:
                if name == "scrape_theme":
                    logger.info("Executing scrape_theme tool")
                    result = await self._scrape_theme(arguments or {})
                    logger.info("scrape_theme tool completed successfully")
                    return result
                elif name == "list_templates":
                    logger.info("Executing list_templates tool")
                    result = await self._list_templates(arguments or {})
                    logger.info("list_templates tool completed successfully")
                    return result
                elif name == "validate_deck":
                    logger.info("Executing validate_deck tool")
                    result = await self._validate_deck(arguments or {})
                    logger.info("validate_deck tool completed successfully")
                    return result
                elif name == "generate_presentation":
                    logger.info("Executing generate_presentation tool")
                    result = await self._generate_presentation(arguments or {})
                    logger.info("generate_presentation tool completed successfully")
                    return result
                elif name == "merge_themes":
                    logger.info("Executing merge_themes tool")
                    result = await self._merge_themes(arguments or {})
                    logger.info("merge_themes tool completed successfully")
                    return result
                else:
                    logger.error(f"Unknown tool requested: {name}")
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.exception(f"Error calling tool {name}")
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "ok": False,
                                "error": str(e),
                                "tool": name
                            })
                        )
                    ]
                )

    async def _scrape_theme(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Extract theme from website."""
        url = arguments["url"]
        extract_logo = arguments.get("extract_logo", True)
        selector_hints = arguments.get("selector_hints")
        
        logger.info(f"Scraping theme from URL: {url}")
        logger.debug(f"Extract logo: {extract_logo}, Selector hints: {selector_hints}")

        theme = await self.theme_extractor.extract_theme(
            url=url,
            extract_logo=extract_logo,
            selector_hints=selector_hints
        )

        logger.info(f"Successfully extracted theme from {url} - Primary color: {theme.colors.primary}, Heading font: {theme.fonts.heading}, Logo: {'Yes' if theme.logo else 'No'}")

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(theme.model_dump(mode='json'), indent=2)
                )
            ]
        )

    async def _list_templates(self, arguments: Dict[str, Any]) -> CallToolResult:
        """List available templates."""
        logger.info("Listing available presentation templates")
        templates = await self.renderer.list_templates()
        logger.info(f"Found {len(templates)} available templates")
        
        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps({"templates": templates}, indent=2)
                )
            ]
        )

    async def _validate_deck(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Validate deck specification."""
        deck_spec_data = arguments["deck_spec"]
        
        logger.info("Validating deck specification")
        logger.debug(f"Deck spec data keys: {list(deck_spec_data.keys()) if isinstance(deck_spec_data, dict) else 'Not a dict'}")
        
        try:
            deck_spec = DeckSpec.model_validate(deck_spec_data)
            logger.info(f"Deck spec validated successfully - {len(deck_spec.slides)} slides")
            validation_result = await self.validator.validate_deck(deck_spec)
            logger.info(f"Validation complete - Valid: {validation_result.valid}, Errors: {len(validation_result.errors)}, Warnings: {len(validation_result.warnings)}")
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(validation_result.model_dump(mode='json'), indent=2)
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Deck validation failed: {str(e)}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "valid": False,
                            "errors": [f"Schema validation failed: {str(e)}"],
                            "warnings": [],
                            "suggestions": []
                        }, indent=2)
                    )
                ]
            )

    async def _generate_presentation(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Generate PowerPoint presentation."""
        deck_spec_data = arguments["deck_spec"]
        
        logger.info("Starting presentation generation")
        logger.debug(f"Deck spec data keys: {list(deck_spec_data.keys()) if isinstance(deck_spec_data, dict) else 'Not a dict'}")
        
        try:
            deck_spec = DeckSpec.model_validate(deck_spec_data)
            logger.info(f"Starting generation of presentation with {len(deck_spec.slides)} slides")
            result = await self.renderer.generate_presentation(deck_spec)
            logger.info(f"Presentation generation completed successfully. Output: {result.get('output', 'Unknown')}")
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Presentation generation failed: {str(e)}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "ok": False,
                            "error": str(e),
                            "output": None,
                            "slides_generated": 0,
                            "warnings": [],
                            "assets_downloaded": []
                        }, indent=2)
                    )
                ]
            )

    async def _merge_themes(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Merge multiple themes."""
        themes_data = arguments["themes"]
        priority = arguments.get("priority", "balanced")
        
        logger.info(f"Merging {len(themes_data)} themes with priority: {priority}")
        
        try:
            themes = [ScrapedTheme.model_validate(theme) for theme in themes_data]
            logger.info(f"Successfully validated {len(themes)} theme objects")
            merged_theme = self.theme_extractor.merge_themes(themes, priority)
            logger.info("Theme merging completed successfully")
            
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "merged_theme": merged_theme.model_dump(mode='json'),
                            "decisions": []  # TODO: Implement decision tracking
                        }, indent=2)
                    )
                ]
            )
        except Exception as e:
            logger.error(f"Theme merging failed: {str(e)}")
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": str(e),
                            "merged_theme": None,
                            "decisions": []
                        }, indent=2)
                    )
                ]
            )

    async def run(self) -> None:
        """Run the MCP server."""
        from mcp.server.stdio import stdio_server

        logger.info("Starting MCP-PPTX server...")

        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("STDIO server started, beginning MCP communication")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="mcp-pptx",
                        server_version="0.1.0",
                        capabilities=ServerCapabilities(
                            tools={}
                        )
                    )
                )
                logger.info("MCP server finished running")
        except BaseException as e:
            # Handle both regular exceptions and ExceptionGroups
            if isinstance(e, BaseExceptionGroup):
                # Check if all exceptions are BrokenPipeError or ConnectionError
                is_disconnect = all(
                    isinstance(exc, (BrokenPipeError, ConnectionError))
                    for exc in e.exceptions
                )
                if is_disconnect:
                    logger.debug("Client disconnected during shutdown")
                    return
            elif isinstance(e, (BrokenPipeError, ConnectionError)):
                # Single BrokenPipeError or ConnectionError
                logger.debug("Client disconnected")
                return
            # Re-raise if it's not a disconnect error
            raise


def suppress_broken_pipe_errors() -> None:
    """Suppress BrokenPipeError during stdout/stderr cleanup."""
    # This prevents the "Exception ignored on flushing sys.stdout" message
    # when the client disconnects before the server finishes cleanup
    if sys.stdout is not None:
        try:
            # Replace stdout flush with one that ignores BrokenPipeError
            original_flush = sys.stdout.flush
            def safe_flush():
                try:
                    original_flush()
                except (BrokenPipeError, OSError):
                    pass  # Ignore pipe errors during cleanup
            sys.stdout.flush = safe_flush
        except AttributeError:
            pass

    if sys.stderr is not None:
        try:
            original_flush = sys.stderr.flush
            def safe_flush():
                try:
                    original_flush()
                except (BrokenPipeError, OSError):
                    pass
            sys.stderr.flush = safe_flush
        except AttributeError:
            pass


async def main() -> None:
    """Main entry point."""
    # Suppress broken pipe errors during cleanup
    suppress_broken_pipe_errors()

    # Set logging level based on environment variable
    log_level = logging.DEBUG if os.getenv('MCP_PPTX_DEBUG', '').lower() in ('1', 'true', 'yes') else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if log_level == logging.DEBUG:
        logger.info("=== MCP-PPTX Server Starting (DEBUG MODE) ===")
        logger.debug("Debug logging enabled via MCP_PPTX_DEBUG environment variable")
    else:
        logger.info("=== MCP-PPTX Server Starting ===")
        logger.info("Set MCP_PPTX_DEBUG=1 for debug logging")

    try:
        server = MCPPPTXServer()
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except BaseException as e:
        # Handle both regular exceptions and ExceptionGroups
        if isinstance(e, BaseExceptionGroup):
            # Check if all exceptions are disconnect-related
            is_disconnect = all(
                isinstance(exc, (BrokenPipeError, ConnectionError))
                for exc in e.exceptions
            )
            if is_disconnect:
                logger.debug("Client disconnected during shutdown")
            else:
                # Some other error occurred
                logger.exception(f"Server failed with error: {e}")
                raise
        elif isinstance(e, (BrokenPipeError, ConnectionError)):
            # Single disconnect error
            logger.debug("Client disconnected")
        elif isinstance(e, KeyboardInterrupt):
            # Already handled above, but just in case
            pass
        else:
            # Unexpected error
            logger.exception(f"Server failed with error: {e}")
            raise
    finally:
        logger.info("=== MCP-PPTX Server Shutdown ===")


if __name__ == "__main__":
    asyncio.run(main())