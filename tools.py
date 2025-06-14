"""
Tool implementations for API Tester MCP Server
"""

import json
import time
from typing import Any, Dict, List
import requests
import mcp.types as types
from config import config
from storage import storage

# ===== HELPER FUNCTIONS =====
def format_response(response: requests.Response) -> Dict[str, Any]:
    """Format response for display"""
    try:
        # Try to parse as JSON
        content = response.json()
    except json.JSONDecodeError:
        content = response.text
    
    return {
        'status_code': response.status_code,
        'status_text': response.reason,
        'headers': dict(response.headers),
        'content': content,
        'size': len(response.content),
        'time_ms': getattr(response, 'elapsed', None).total_seconds() * 1000 if hasattr(response, 'elapsed') else None,
        'url': response.url
    }

def format_request_summary(method: str, url: str, status_code: int, time_ms: float) -> str:
    """Create a nice summary of the request"""
    status_emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "⚠️"
    return f"{status_emoji} {method} {url} → {status_code} ({time_ms:.0f}ms)"

def validate_url(url: str) -> bool:
    """Validate URL format and check against restrictions"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        return config.is_url_allowed(url)
    except:
        return False

def prepare_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Prepare headers by merging with defaults"""
    final_headers = config.get_default_headers()
    if headers:
        final_headers.update(headers)
    return final_headers

# ===== TOOL IMPLEMENTATIONS =====
async def send_request_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Send an HTTP request"""
    method = args["method"].upper()
    url = args["url"]
    headers = prepare_headers(args.get("headers", {}))
    body = args.get("body")
    params = args.get("params", {})
    timeout = args.get("timeout", config.DEFAULT_TIMEOUT)
    
    # Validate URL
    if not validate_url(url):
        return [types.TextContent(
            type="text",
            text=f"❌ Invalid or blocked URL: {url}"
        )]
    
    # Prepare request data
    request_data = {
        "method": method,
        "url": url,
        "headers": headers,
        "params": params,
        "timeout": timeout
    }
    
    if body:
        request_data["body"] = body
        # Try to parse body as JSON for proper content-type
        try:
            json.loads(body)
            if "content-type" not in [k.lower() for k in headers.keys()]:
                headers["Content-Type"] = "application/json"
        except json.JSONDecodeError:
            pass
    
    try:
        start_time = time.time()
        
        # Make the request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            data=body,
            params=params,
            timeout=timeout,
            stream=True  # For large responses
        )
        
        # Check response size
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > config.MAX_RESPONSE_SIZE:
            response.close()
            return [types.TextContent(
                type="text",
                text=f"❌ Response too large ({content_length} bytes). Max allowed: {config.MAX_RESPONSE_SIZE} bytes"
            )]
        
        end_time = time.time()
        time_ms = (end_time - start_time) * 1000
        
        # Format response
        response_data = format_response(response)
        response_data["time_ms"] = time_ms
        
        # Add to history
        storage.add_to_history(request_data, response_data)
        
        # Create summary
        summary = format_request_summary(method, url, response.status_code, time_ms)
        
        # Format detailed response
        result = f"{summary}\n\n"
        result += f"**Response Details:**\n"
        result += f"• Status: {response.status_code} {response.reason}\n"
        result += f"• Size: {response_data['size']} bytes\n"
        result += f"• Time: {time_ms:.0f}ms\n\n"
        
        if response_data['headers']:
            result += "**Headers:**\n"
            for key, value in response_data['headers'].items():
                result += f"• {key}: {value}\n"
            result += "\n"
        
        result += "**Content:**\n"
        if isinstance(response_data['content'], dict):
            result += f"```json\n{json.dumps(response_data['content'], indent=2)}\n```"
        else:
            content_preview = str(response_data['content'])[:config.RESPONSE_PREVIEW_LENGTH]
            if len(str(response_data['content'])) > config.RESPONSE_PREVIEW_LENGTH:
                content_preview += "... (truncated)"
            result += f"```\n{content_preview}\n```"
        
        return [types.TextContent(type="text", text=result)]
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ Request failed: {str(e)}"
        
        # Add failed request to history
        error_response = {
            "error": str(e),
            "status_code": None,
            "time_ms": None
        }
        storage.add_to_history(request_data, error_response)
        
        return [types.TextContent(type="text", text=error_msg)]

async def save_request_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Save a request configuration"""
    name = args["name"]
    
    # Check if name already exists
    if storage.get_request(name):
        return [types.TextContent(
            type="text",
            text=f"❌ Request '{name}' already exists. Use update_request to modify it."
        )]
    
    request_config = {
        "method": args["method"],
        "url": args["url"],
        "headers": args.get("headers", {}),
        "body": args.get("body"),
        "params": args.get("params", {}),
        "description": args.get("description", "")
    }
    
    storage.save_request(name, request_config)
    
    result = f"✅ Saved request '{name}'\n\n"
    result += f"**Configuration:**\n"
    result += f"• Method: {request_config['method']}\n"
    result += f"• URL: {request_config['url']}\n"
    if request_config['description']:
        result += f"• Description: {request_config['description']}\n"
    
    return [types.TextContent(type="text", text=result)]

async def load_request_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Load and execute a saved request"""
    name = args["name"]
    overrides = args.get("override_params", {})
    
    saved_request = storage.get_request(name)
    if not saved_request:
        available = storage.list_saved_requests()
        suggestion = f"\n\nAvailable requests: {', '.join(available)}" if available else ""
        return [types.TextContent(
            type="text", 
            text=f"❌ No saved request found with name '{name}'{suggestion}"
        )]
    
    # Merge saved request with overrides
    request_args = {**saved_request, **overrides}
    
    # Remove metadata fields
    request_args.pop("saved_at", None)
    request_args.pop("updated_at", None)
    request_args.pop("description", None)
    request_args.pop("id", None)
    
    # Execute the request
    result_text = f"🔄 Loading and executing saved request '{name}'...\n\n"
    execution_result = await send_request_tool(request_args)
    
    return [types.TextContent(
        type="text",
        text=result_text + execution_result[0].text
    )]

async def update_request_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Update an existing saved request"""
    name = args["name"]
    
    if not storage.get_request(name):
        return [types.TextContent(
            type="text",
            text=f"❌ No saved request found with name '{name}'"
        )]
    
    # Prepare update data (only include provided fields)
    update_data = {}
    for field in ["method", "url", "headers", "body", "params", "description"]:
        if field in args:
            update_data[field] = args[field]
    
    if storage.update_request(name, update_data):
        result = f"✅ Updated request '{name}'\n\n"
        result += "**Updated fields:**\n"
        for field, value in update_data.items():
            result += f"• {field}: {value}\n"
        
        return [types.TextContent(type="text", text=result)]
    else:
        return [types.TextContent(
            type="text",
            text=f"❌ Failed to update request '{name}'"
        )]

async def delete_request_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Delete a saved request"""
    name = args["name"]
    
    if storage.delete_request(name):
        return [types.TextContent(
            type="text",
            text=f"✅ Deleted saved request '{name}'"
        )]
    else:
        available = storage.list_saved_requests()
        suggestion = f"\n\nAvailable requests: {', '.join(available)}" if available else ""
        return [types.TextContent(
            type="text",
            text=f"❌ No saved request found with name '{name}'{suggestion}"
        )]

async def list_requests_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """List all saved requests"""
    requests_summary = storage.get_saved_requests_summary()
    
    if not requests_summary:
        return [types.TextContent(
            type="text",
            text="📭 No saved requests found. Use 'save_request' to create some!"
        )]
    
    result = f"📋 **Saved Requests ({len(requests_summary)}):**\n\n"
    
    for req in requests_summary:
        result += f"**{req['name']}**\n"
        result += f"• Method: {req['method']}\n"
        result += f"• URL: {req['url']}\n"
        if req['description']:
            result += f"• Description: {req['description']}\n"
        result += f"• Saved: {req['saved_at']}\n\n"
    
    return [types.TextContent(type="text", text=result)]

async def analyze_response_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Analyze the last response"""
    if not storage.history:
        return [types.TextContent(
            type="text",
            text="❌ No request history available to analyze"
        )]
    
    last_entry = storage.history[0]
    response_data = last_entry["response"]
    
    if "error" in response_data:
        return [types.TextContent(
            type="text",
            text="❌ Cannot analyze failed request"
        )]
    
    extract_path = args.get("extract_path")
    content = response_data.get("content")
    
    result = "**Response Analysis:**\n\n"
    
    # Basic info
    result += f"• Status: {response_data['status_code']}\n"
    result += f"• Content Type: {response_data.get('content_type', 'unknown')}\n"
    result += f"• Size: {response_data['size']} bytes\n"
    result += f"• Response Time: {response_data.get('time_ms', 0):.0f}ms\n\n"
    
    # Extract specific data if requested
    if extract_path and isinstance(content, dict):
        try:
            # Simple path extraction (supports dot notation and array access)
            value = content
            for key in extract_path.split('.'):
                if '[' in key and ']' in key:
                    # Handle array access like 'users[0]'
                    array_key = key.split('[')[0]
                    index = int(key.split('[')[1].split(']')[0])
                    value = value[array_key][index]
                else:
                    value = value[key]
            
            result += f"**Extracted Value ({extract_path}):**\n"
            if isinstance(value, (dict, list)):
                result += f"```json\n{json.dumps(value, indent=2)}\n```"
            else:
                result += f"`{value}`"
        
        except (KeyError, IndexError, ValueError, TypeError) as e:
            result += f"❌ Could not extract '{extract_path}': {str(e)}"
    
    return [types.TextContent(type="text", text=result)]

async def view_history_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """View request history"""
    limit = args.get("limit", 10)
    method_filter = args.get("method")
    url_filter = args.get("url")
    
    # Get filtered history
    if url_filter:
        history = storage.get_history_by_url(url_filter, limit)
    elif method_filter:
        history = storage.get_history_by_method(method_filter, limit)
    else:
        history = storage.get_history(limit)
    
    if not history:
        return [types.TextContent(
            type="text",
            text="📭 No request history found"
        )]
    
    result = f"📊 **Request History ({len(history)} entries):**\n\n"
    
    for entry in history:
        req = entry['request']
        resp = entry['response']
        
        status_emoji = "✅" if resp.get('status_code', 0) < 400 else "❌"
        result += f"{status_emoji} **{req['method']} {req['url']}**\n"
        result += f"• Time: {entry['timestamp']}\n"
        result += f"• Status: {resp.get('status_code', 'Error')}\n"
        if resp.get('time_ms'):
            result += f"• Duration: {resp['time_ms']:.0f}ms\n"
        result += "\n"
    
    return [types.TextContent(type="text", text=result)]

async def get_stats_tool(args: Dict[str, Any]) -> List[types.TextContent]:
    """Get API testing statistics"""
    stats = storage.get_stats()
    
    result = "📊 **API Testing Statistics:**\n\n"
    result += f"• Total Requests: {stats['total_requests']}\n"
    result += f"• Saved Configurations: {stats['saved_requests']}\n"
    result += f"• Success Rate: {stats['success_rate']}%\n\n"
    
    if stats['common_methods']:
        result += "**Most Used Methods:**\n"
        for method, count in stats['common_methods'].items():
            result += f"• {method}: {count} requests\n"
        result += "\n"
    
    if stats['common_domains']:
        result += "**Most Tested Domains:**\n"
        for domain, count in stats['common_domains'].items():
            result += f"• {domain}: {count} requests\n"
    
    return [types.TextContent(type="text", text=result)]

# ===== TOOL DEFINITIONS =====
TOOL_DEFINITIONS = [
    {
        "name": "send_request",
        "description": "Send an HTTP request to any API endpoint",
        "inputSchema": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                    "description": "HTTP method to use"
                },
                "url": {
                    "type": "string",
                    "description": "Full URL to send the request to"
                },
                "headers": {
                    "type": "object",
                    "description": "HTTP headers as key-value pairs",
                    "additionalProperties": {"type": "string"}
                },
                "body": {
                    "type": "string",
                    "description": "Request body (JSON string or plain text)"
                },
                "params": {
                    "type": "object",
                    "description": "URL query parameters as key-value pairs",
                    "additionalProperties": {"type": "string"}
                },
                "timeout": {
                    "type": "number",
                    "description": f"Request timeout in seconds (default: {config.DEFAULT_TIMEOUT})",
                    "default": config.DEFAULT_TIMEOUT
                }
            },
            "required": ["method", "url"]
        }
    },
    {
        "name": "save_request",
        "description": "Save a request configuration for later reuse",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name to save the request as"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]},
                "url": {"type": "string", "description": "URL for the request"},
                "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                "body": {"type": "string", "description": "Request body"},
                "params": {"type": "object", "additionalProperties": {"type": "string"}},
                "description": {"type": "string", "description": "Description of what this request does"}
            },
            "required": ["name", "method", "url"]
        }
    },
    {
        "name": "load_request",
        "description": "Load and execute a previously saved request",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the saved request to load"},
                "override_params": {"type": "object", "description": "Override specific parameters"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_request",
        "description": "Update an existing saved request",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name of the request to update"},
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]},
                "url": {"type": "string"},
                "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                "body": {"type": "string"},
                "params": {"type": "object", "additionalProperties": {"type": "string"}},
                "description": {"type": "string"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "delete_request",
        "description": "Delete a saved request",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Name of the saved request to delete"}},
            "required": ["name"]
        }
    },
    {
        "name": "list_requests",
        "description": "List all saved request configurations",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "analyze_response",
        "description": "Analyze and extract data from the last response",
        "inputSchema": {
            "type": "object",
            "properties": {
                "extract_path": {"type": "string", "description": "JSON path to extract (e.g., 'data.users[0].name')"},
                "validate_schema": {"type": "object", "description": "JSON schema to validate response against"}
            },
            "required": []
        }
    },
    {
        "name": "view_history",
        "description": "View recent request history with optional filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "number", "description": "Number of entries to show (default: 10)", "default": 10},
                "method": {"type": "string", "description": "Filter by HTTP method"},
                "url": {"type": "string", "description": "Filter by exact URL"}
            },
            "required": []
        }
    },
    {
        "name": "get_stats",
        "description": "Get API testing statistics and usage summary",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    }
]

# Tool execution mapping
TOOL_HANDLERS = {
    "send_request": send_request_tool,
    "save_request": save_request_tool,
    "load_request": load_request_tool,
    "update_request": update_request_tool,
    "delete_request": delete_request_tool,
    "list_requests": list_requests_tool,
    "analyze_response": analyze_response_tool,
    "view_history": view_history_tool,
    "get_stats": get_stats_tool
}