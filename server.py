#!/usr/bin/env python3
"""
API Tester MCP Server - Modular Version
Clean server setup using organized modules
"""

import asyncio
import json
from typing import Any, Dict, List
import mcp.server.stdio
import mcp.types as types
from mcp.server import Server

# Import our modules
from config import config, get_environment_config, list_environments
from storage import storage
from tools import TOOL_DEFINITIONS, TOOL_HANDLERS
from prompts import PROMPT_DEFINITIONS, PROMPT_HANDLERS

# ===== SERVER SETUP =====
server = Server(config.SERVER_NAME)

# ===== TOOL HANDLERS =====
@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List all available API testing tools"""
    return [
        types.Tool(
            name=tool_def["name"],
            description=tool_def["description"],
            inputSchema=tool_def["inputSchema"]
        )
        for tool_def in TOOL_DEFINITIONS
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool execution by delegating to appropriate handler"""
    try:
        if name in TOOL_HANDLERS:
            return await TOOL_HANDLERS[name](arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        error_msg = f"❌ Error executing {name}: {str(e)}"
        if config.DEBUG:
            import traceback
            error_msg += f"\n\nDebug info:\n{traceback.format_exc()}"
        
        return [types.TextContent(type="text", text=error_msg)]

# ===== RESOURCE HANDLERS =====
@server.list_resources()
async def handle_list_resources() -> List[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="saved-requests://list",
            name="Saved Requests",
            description="List of all saved request configurations",
            mimeType="application/json"
        ),
        types.Resource(
            uri="history://recent",
            name="Request History",
            description="Recent request/response history",
            mimeType="application/json"
        ),
        types.Resource(
            uri="stats://summary",
            name="Usage Statistics",
            description="API testing usage statistics and metrics",
            mimeType="application/json"
        ),
        types.Resource(
            uri="config://environments",
            name="Environments",
            description="Available environment configurations",
            mimeType="application/json"
        ),
        types.Resource(
            uri="config://settings",
            name="Server Settings",
            description="Current server configuration",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle resource reading"""
    
    if uri == "saved-requests://list":
        requests_summary = storage.get_saved_requests_summary()
        if not requests_summary:
            return json.dumps({"message": "No saved requests", "requests": []})
        
        return json.dumps({
            "total": len(requests_summary),
            "requests": requests_summary
        }, indent=2)
    
    elif uri == "history://recent":
        history = storage.get_history(20)
        if not history:
            return json.dumps({"message": "No request history", "history": []})
        
        # Format for display
        formatted = []
        for entry in history:
            formatted.append({
                "id": entry.get("id"),
                "timestamp": entry["timestamp"],
                "request": {
                    "method": entry["request"]["method"],
                    "url": entry["request"]["url"],
                    "has_body": entry["request"].get("has_body", False)
                },
                "response": {
                    "status_code": entry["response"].get("status_code"),
                    "time_ms": entry["response"].get("time_ms"),
                    "size": entry["response"].get("size"),
                    "success": entry["response"].get("status_code", 0) < 400
                }
            })
        
        return json.dumps({
            "total": len(formatted),
            "history": formatted
        }, indent=2)
    
    elif uri == "stats://summary":
        stats = storage.get_stats()
        return json.dumps(stats, indent=2)
    
    elif uri == "config://environments":
        environments = {}
        for env_name in list_environments():
            environments[env_name] = get_environment_config(env_name)
        
        return json.dumps({
            "available_environments": environments,
            "usage": "Use environment names with requests to automatically set base URLs"
        }, indent=2)
    
    elif uri == "config://settings":
        settings = {
            "server_name": config.SERVER_NAME,
            "server_version": config.SERVER_VERSION,
            "debug": config.DEBUG,
            "default_timeout": config.DEFAULT_TIMEOUT,
            "max_history": config.MAX_HISTORY,
            "max_response_size": config.MAX_RESPONSE_SIZE,
            "response_preview_length": config.RESPONSE_PREVIEW_LENGTH,
            "save_to_files": config.SAVE_REQUESTS_TO_FILE,
            "allowed_domains": config.ALLOWED_DOMAINS,
            "blocked_domains": config.BLOCKED_DOMAINS
        }
        
        return json.dumps(settings, indent=2)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

# ===== PROMPT HANDLERS =====
@server.list_prompts()
async def handle_list_prompts() -> List[types.Prompt]:
    """List available prompts"""
    return [
        types.Prompt(
            name=prompt_def["name"],
            description=prompt_def["description"],
            arguments=prompt_def["arguments"]
        )
        for prompt_def in PROMPT_DEFINITIONS
    ]

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: Dict[str, str] | None) -> types.GetPromptResult:
    """Handle prompt generation by delegating to appropriate handler"""
    try:
        if name in PROMPT_HANDLERS:
            return await PROMPT_HANDLERS[name](arguments)
        else:
            raise ValueError(f"Unknown prompt: {name}")
    
    except Exception as e:
        # Return a basic error result if prompt generation fails
        return types.GetPromptResult(
            description=f"Error generating prompt: {name}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=f"❌ Error generating prompt '{name}': {str(e)}"
                    )
                )
            ]
        )

# ===== STARTUP VALIDATION =====
def validate_startup():
    """Validate configuration and dependencies on startup"""
    if not config.validate_config():
        print("❌ Configuration validation failed!")
        return False
    
    # Test storage
    try:
        storage.get_stats()
        print("✅ Storage system initialized")
    except Exception as e:
        print(f"❌ Storage initialization failed: {e}")
        return False
    
    print(f"✅ {config.SERVER_NAME} v{config.SERVER_VERSION} initialized")
    print(f"   Debug mode: {config.DEBUG}")
    print(f"   Max history: {config.MAX_HISTORY}")
    print(f"   Default timeout: {config.DEFAULT_TIMEOUT}s")
    print(f"   Save to files: {config.SAVE_REQUESTS_TO_FILE}")
    
    return True

# ===== MAIN SERVER RUNNER =====
async def main():
    """Run the MCP server"""
    if not validate_startup():
        print("❌ Server startup validation failed!")
        return
    
    print("🚀 Starting API Tester MCP Server...")
    print("📡 Connect this server to Claude Desktop to start testing APIs!")
    print("📚 Use prompts for guided API testing workflows")
    
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())