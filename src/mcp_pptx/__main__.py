"""Main entry point for MCP-PPTX server."""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())