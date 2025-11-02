#!/usr/bin/env python3
"""Test script to verify MCP server functionality."""

import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp_pptx.server import MCPPPTXServer


async def test_server_tools():
    """Test server tool functionality directly."""
    print("Testing MCP-PPTX Server Tools")
    print("=" * 40)
    
    server = MCPPPTXServer()
    
    # Test 1: List tools
    print("\n1. Testing list_templates tool...")
    try:
        result = await server._list_templates({})
        print("✅ list_templates works")
        response = json.loads(result.content[0].text)
        print(f"   Found {len(response['templates'])} templates")
    except Exception as e:
        print(f"❌ list_templates failed: {e}")
    
    # Test 2: Test validation with a simple deck
    print("\n2. Testing validate_deck tool...")
    try:
        simple_deck = {
            "title": "Test Presentation",
            "theme": {
                "template": "themes/default.potx"
            },
            "slides": [
                {
                    "title": "Test Slide",
                    "layout": "TITLE_CONTENT",
                    "content": []
                }
            ]
        }
        
        result = await server._validate_deck({"deck_spec": simple_deck})
        print("✅ validate_deck works")
        response = json.loads(result.content[0].text)
        print(f"   Valid: {response.get('valid', False)}")
        if response.get('warnings'):
            print(f"   Warnings: {len(response['warnings'])}")
    except Exception as e:
        print(f"❌ validate_deck failed: {e}")
    
    # Test 3: Test theme merging
    print("\n3. Testing merge_themes tool...")
    try:
        themes = [
            {
                "colors": {
                    "primary": "#005596",
                    "secondary": "#0A77C0",
                    "accent": "#FF5733",
                    "background": "#FFFFFF",
                    "text": "#333333"
                },
                "fonts": {
                    "heading": "Calibri Light",
                    "body": "Arial"
                },
                "source_url": "https://example1.com",
                "warnings": []
            }
        ]
        
        result = await server._merge_themes({"themes": themes, "priority": "first"})
        print("✅ merge_themes works")
        response = json.loads(result.content[0].text)
        print(f"   Merged theme created successfully")
    except Exception as e:
        print(f"❌ merge_themes failed: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Server functionality test complete!")


if __name__ == "__main__":
    asyncio.run(test_server_tools())