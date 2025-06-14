# API Tester MCP Server

A powerful **Model Context Protocol (MCP) server** designed for comprehensive API testing, exploration, and debugging. This server provides Claude with specialized tools and guided prompts to systematically test, analyze, and document APIs.

## 🚀 Features

### 🔧 Comprehensive API Testing Tools
- **HTTP Requests**: Full support for GET, POST, PUT, DELETE, PATCH, and more
- **Authentication**: Bearer tokens, API keys, Basic auth, and custom headers
- **Request Management**: Save, load, and organize request configurations
- **Response Analysis**: Detailed response inspection with headers, timing, and size metrics
- **Environment Support**: Multiple environment configurations for different stages

### 📊 Advanced Analysis & Debugging
- **Request History**: Track and analyze all API interactions
- **Response Comparison**: Compare responses across different requests
- **Statistics**: Usage metrics and performance insights
- **Error Analysis**: Detailed error reporting and debugging assistance

### 🎯 Guided Workflows
- **Smart Prompts**: Step-by-step guides for API exploration and testing
- **Debugging Assistance**: Systematic approach to troubleshooting failed requests
- **Load Test Planning**: Strategy development for performance testing
- **API Documentation**: Automated documentation generation from testing sessions

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- Claude Desktop application

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd API-Tester
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Claude Desktop**:
   Add the following to your Claude Desktop MCP settings (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "api-tester": {
         "command": "python",
         "args": ["/path/to/your/API-Tester/server.py"],
         "env": {
           "DEBUG": "false"
         }
       }
     }
   }
   ```

5. **Start the server**:
   ```bash
   python server.py
   ```

## 🛠️ Available Tools

### Core Testing Tools
- **`make_request`** - Execute HTTP requests with full configuration options
- **`save_request`** - Save request configurations for reuse
- **`load_request`** - Load and execute saved request configurations
- **`delete_request`** - Remove saved request configurations

### Analysis Tools
- **`get_history`** - Retrieve and analyze request history
- **`compare_responses`** - Compare responses from different requests
- **`analyze_response`** - Deep analysis of response data and patterns
- **`get_stats`** - Usage statistics and performance metrics

### Management Tools
- **`list_requests`** - View all saved request configurations
- **`set_environment`** - Switch between different environment configurations
- **`clear_history`** - Clean up request history

## 📝 Available Prompts

### 🧪 `test_api`
Comprehensive guide for testing a new API endpoint
- **Parameters**: `api_url` (required), `api_type`, `auth_type`
- **Use Case**: Systematic testing of new or unknown APIs

### 🐛 `debug_request`
Help debug failing API requests
- **Parameters**: `error_message` (required), `request_method`
- **Use Case**: Troubleshooting failed requests and error analysis

### 🔍 `api_exploration`
Systematically explore and document an API
- **Parameters**: `base_url` (required), `documentation_url`
- **Use Case**: Discovery and mapping of API endpoints and capabilities

### 🚀 `load_test_planning`
Plan a load testing strategy for an API
- **Parameters**: `endpoint_url` (required), `expected_load`
- **Use Case**: Performance testing strategy development

## ⚙️ Configuration

### Environment Variables
- **`DEBUG`** - Enable debug mode for detailed logging
- **`MAX_HISTORY`** - Maximum number of requests to keep in history (default: 100)
- **`DEFAULT_TIMEOUT`** - Default request timeout in seconds (default: 30)
- **`SAVE_REQUESTS_TO_FILE`** - Save requests to persistent storage (default: true)

### Environment Configurations
The server supports multiple environment configurations for different deployment stages:

```python
# Example environment setup
environments = {
    "development": {
        "base_url": "http://localhost:3000/api",
        "timeout": 30
    },
    "staging": {
        "base_url": "https://staging.example.com/api",
        "timeout": 60
    },
    "production": {
        "base_url": "https://api.example.com",
        "timeout": 30
    }
}
```

## 📖 Usage Examples

### Basic API Request
```
Use the make_request tool to test a GET endpoint:
- URL: https://jsonplaceholder.typicode.com/posts/1
- Method: GET
- Save as: "test-post-endpoint"
```

### Authentication Testing
```
Test an authenticated endpoint:
- URL: https://api.github.com/user
- Method: GET
- Headers: {"Authorization": "Bearer YOUR_TOKEN"}
- Save as: "github-user-auth"
```

### Request Analysis
```
After making requests, use:
- get_history: Review recent requests and responses
- analyze_response: Deep dive into response patterns
- compare_responses: Compare different API responses
```

### Guided API Exploration
```
Use the "api_exploration" prompt with:
- base_url: https://api.example.com
- documentation_url: https://docs.example.com/api
```

## 🏗️ Project Structure

```
API-Tester/
├── server.py          # Main MCP server implementation
├── config.py          # Configuration management and validation
├── storage.py         # Data persistence and history management
├── tools.py           # API testing tool implementations
├── prompts.py         # Guided workflow prompts
├── requirements.txt   # Python dependencies
└── README.md          # Project documentation
```

## 🔧 Development

### Adding New Tools
1. Define the tool in `tools.py` in the `TOOL_DEFINITIONS` list
2. Implement the handler function
3. Add to the `TOOL_HANDLERS` dictionary

### Adding New Prompts
1. Define the prompt in `prompts.py` in the `PROMPT_DEFINITIONS` list
2. Implement the handler function
3. Add to the `PROMPT_HANDLERS` dictionary

### Configuration Options
Modify `config.py` to add new configuration parameters and validation rules.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Please see the LICENSE file for details.

## 🆘 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check the debug logs when `DEBUG=true`
- Review the request history for troubleshooting

## 🎯 Use Cases

- **API Development**: Test and validate APIs during development
- **API Integration**: Explore and understand third-party APIs
- **Quality Assurance**: Systematic testing of API endpoints
- **Documentation**: Generate API documentation from testing sessions
- **Debugging**: Troubleshoot API integration issues
- **Performance Testing**: Plan and validate API performance strategies

---

**Ready to start testing APIs with Claude?** 🚀

Connect this MCP server to Claude Desktop and use the guided prompts to systematically explore, test, and document any API!
