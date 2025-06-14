#!/usr/bin/env python3
"""
API Tester MCP Server - Prompts Module
Handles all prompt definitions and generation logic
"""

from typing import Dict, List
import mcp.types as types

# ===== PROMPT DEFINITIONS =====
PROMPT_DEFINITIONS = [
    {
        "name": "test_api",
        "description": "Comprehensive guide for testing a new API endpoint",
        "arguments": [
            types.PromptArgument(
                name="api_url",
                description="The API endpoint URL to test",
                required=True
            ),
            types.PromptArgument(
                name="api_type",
                description="Type of API (REST, GraphQL, etc.)",
                required=False
            ),
            types.PromptArgument(
                name="auth_type",
                description="Authentication type expected (Bearer, API Key, etc.)",
                required=False
            )
        ]
    },
    {
        "name": "debug_request",
        "description": "Help debug a failing API request",
        "arguments": [
            types.PromptArgument(
                name="error_message",
                description="The error message you're seeing",
                required=True
            ),
            types.PromptArgument(
                name="request_method",
                description="HTTP method used (GET, POST, etc.)",
                required=False
            )
        ]
    },
    {
        "name": "api_exploration",
        "description": "Systematically explore and document an API",
        "arguments": [
            types.PromptArgument(
                name="base_url",
                description="Base URL of the API to explore",
                required=True
            ),
            types.PromptArgument(
                name="documentation_url",
                description="URL to API documentation (if available)",
                required=False
            )
        ]
    },
    {
        "name": "load_test_planning",
        "description": "Plan a load testing strategy for an API",
        "arguments": [
            types.PromptArgument(
                name="endpoint_url",
                description="The endpoint to load test",
                required=True
            ),
            types.PromptArgument(
                name="expected_load",
                description="Expected requests per second/minute",
                required=False
            )
        ]
    }
]

# ===== PROMPT HANDLERS =====
async def handle_test_api_prompt(arguments: Dict[str, str] | None) -> types.GetPromptResult:
    """Generate comprehensive API testing guidance"""
    api_url = arguments.get("api_url", "") if arguments else ""
    api_type = arguments.get("api_type", "REST") if arguments else "REST"
    auth_type = arguments.get("auth_type", "unknown") if arguments else "unknown"
    
    return types.GetPromptResult(
        description="Comprehensive API testing guidance",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"""I want to thoroughly test this {api_type} API endpoint: {api_url}

Please help me create a comprehensive testing plan:

1. **Initial Exploration:**
   - Start with a simple GET request to understand the response format
   - Check response headers for important information (rate limits, versioning, etc.)
   - Identify the response structure and data types

2. **Authentication Testing:**
   - The API appears to use {auth_type} authentication
   - Test both authenticated and unauthenticated requests
   - Verify proper error handling for auth failures

3. **Method Testing:**
   - Test all appropriate HTTP methods (GET, POST, PUT, DELETE, etc.)
   - Verify each method returns expected status codes
   - Test with various payloads and parameters

4. **Edge Case Testing:**
   - Test with invalid parameters
   - Test with missing required fields
   - Test with oversized payloads
   - Test rate limiting behavior

5. **Documentation:**
   - Save successful requests for future reference
   - Document the API's behavior and quirks
   - Create reusable request templates

Use the API testing tools to systematically work through this plan. Save useful configurations with descriptive names."""
                )
            )
        ]
    )

async def handle_debug_request_prompt(arguments: Dict[str, str] | None) -> types.GetPromptResult:
    """Generate request debugging assistance"""
    error_message = arguments.get("error_message", "") if arguments else ""
    request_method = arguments.get("request_method", "unknown") if arguments else "unknown"
    
    return types.GetPromptResult(
        description="Request debugging assistance",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"""I'm encountering this error with a {request_method} request: {error_message}

Please help me debug this systematically:

1. **Error Analysis:**
   - Analyze what this error typically means
   - Identify the most likely causes
   - Suggest immediate troubleshooting steps

2. **Request Review:**
   - Check the request history to see recent attempts
   - Compare with any successful requests to the same endpoint
   - Verify the request format and headers

3. **Systematic Testing:**
   - Test simpler variations of the request
   - Verify the endpoint URL is correct
   - Check authentication and headers
   - Try different payload formats if applicable

4. **Advanced Debugging:**
   - Look for subtle issues (typos, encoding problems, etc.)
   - Test similar requests that work
   - Check for API changes or documentation updates

Use the analysis and history tools to examine recent requests and identify patterns."""
                )
            )
        ]
    )

async def handle_api_exploration_prompt(arguments: Dict[str, str] | None) -> types.GetPromptResult:
    """Generate API exploration strategy"""
    base_url = arguments.get("base_url", "") if arguments else ""
    doc_url = arguments.get("documentation_url", "") if arguments else ""
    
    doc_text = f"\nDocumentation: {doc_url}" if doc_url else "\nNo documentation provided - we'll discover the API structure through testing."
    
    return types.GetPromptResult(
        description="API exploration strategy",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"""Let's systematically explore and document this API: {base_url}{doc_text}

**Exploration Strategy:**

1. **Discovery Phase:**
   - Test the root endpoint ({base_url})
   - Look for common endpoints (/api, /v1, /health, /docs)
   - Check for API metadata or version information

2. **Authentication Discovery:**
   - Test unauthenticated access to understand requirements
   - Try common auth patterns (Bearer tokens, API keys, Basic auth)
   - Document authentication requirements

3. **Endpoint Mapping:**
   - Discover available endpoints through testing
   - Document request/response formats for each
   - Identify required vs optional parameters

4. **Pattern Analysis:**
   - Look for consistent patterns in URLs
   - Document naming conventions
   - Identify resource relationships

5. **Comprehensive Documentation:**
   - Save all working requests with descriptive names
   - Create a summary of the API structure
   - Note any quirks or special behaviors

Save each successful request with a clear name like "api-root", "auth-test", "user-list", etc."""
                )
            )
        ]
    )

async def handle_load_test_planning_prompt(arguments: Dict[str, str] | None) -> types.GetPromptResult:
    """Generate load testing strategy planning"""
    endpoint_url = arguments.get("endpoint_url", "") if arguments else ""
    expected_load = arguments.get("expected_load", "unknown") if arguments else "unknown"
    
    return types.GetPromptResult(
        description="Load testing strategy planning",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(
                    type="text",
                    text=f"""Let's plan a load testing strategy for: {endpoint_url}
Expected load: {expected_load}

**Load Testing Plan:**

1. **Baseline Testing:**
   - First, establish that the endpoint works correctly with single requests
   - Test various scenarios (success cases, error cases)
   - Save working request configurations

2. **Performance Baseline:**
   - Make several individual requests to establish baseline response times
   - Note normal response sizes and patterns
   - Document expected behavior under normal load

3. **Gradual Load Increase:**
   - Plan to increase load gradually
   - Start with low concurrent requests
   - Monitor response times and error rates

4. **Test Scenarios:**
   - Plan different types of requests (read-heavy, write-heavy)
   - Consider authentication load
   - Test edge cases under load

5. **Monitoring Strategy:**
   - Watch for response time degradation
   - Monitor error rate increases
   - Look for rate limiting responses

**Note:** This MCP server is designed for API testing and exploration, not high-volume load testing. For actual load testing, consider tools like Artillery, JMeter, or k6. We can help you prepare and validate your requests here first."""
                )
            )
        ]
    )

# ===== PROMPT HANDLER MAPPING =====
PROMPT_HANDLERS = {
    "test_api": handle_test_api_prompt,
    "debug_request": handle_debug_request_prompt,
    "api_exploration": handle_api_exploration_prompt,
    "load_test_planning": handle_load_test_planning_prompt
} 