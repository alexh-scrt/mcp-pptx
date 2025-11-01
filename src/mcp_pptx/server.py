"""MCP-PPTX Server implementation."""

import asyncio
import json
import logging
import os
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
                        description="Generate a PowerPoint presentation from a deck specification",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "deck_spec": {
                                    "type": "object",
                                    "description": "The deck specification"
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
        
        logger.info(f"Successfully extracted theme with {len(theme.colors) if theme.colors else 0} colors and {len(theme.fonts) if theme.fonts else 0} fonts")

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=json.dumps(theme.model_dump(), indent=2)
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
                        text=json.dumps(validation_result.model_dump(), indent=2)
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
                            "merged_theme": merged_theme.model_dump(),
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


async def main() -> None:
    """Main entry point."""
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
    except Exception as e:
        logger.exception(f"Server failed with error: {e}")
        raise
    finally:
        logger.info("=== MCP-PPTX Server Shutdown ===")


if __name__ == "__main__":
    asyncio.run(main())