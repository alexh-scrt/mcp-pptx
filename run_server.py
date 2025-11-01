#!/usr/bin/env python3
"""Entry point script for MCP-PPTX server."""

import sys
sys.path.insert(0, 'src')

from mcp_pptx.server import main
import asyncio

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

if __name__ == "__main__":
    asyncio.run(main())