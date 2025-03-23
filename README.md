# FastAPI-MCP

A zero-configuration tool for automatically exposing FastAPI endpoints as Model Context Protocol (MCP) tools.

[![PyPI version](https://badge.fury.io/py/fastapi-mcp.svg)](https://pypi.org/project/fastapi-mcp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-mcp.svg)](https://pypi.org/project/fastapi-mcp/)

## Features

- **Direct integration** - Mount an MCP server directly to your FastAPI app
- **Zero configuration** required - just point it at your FastAPI app and it works
- **Automatic discovery** of all FastAPI endpoints and conversion to MCP tools
- **Preserving schemas** of your request models and response models
- **Preserve documentation** of all your endpoints, just as it is in Swagger
- **Extend** - Add custom MCP tools alongside the auto-generated ones
- **Authentication** - Secure your MCP server with various authentication methods

## Installation

We recommend using [uv](https://docs.astral.sh/uv/), a fast Python package installer:

```bash
uv add fastapi-mcp
```

Alternatively, you can install with pip:

```bash
pip install fastapi-mcp
```

## Basic Usage

The simplest way to use FastAPI-MCP is to add an MCP server directly to your FastAPI application:

```python
from fastapi import FastAPI
from fastapi_mcp import add_mcp_server

# Your FastAPI app
app = FastAPI()

# Mount the MCP server to your app
add_mcp_server(
    app,                    # Your FastAPI app
    mount_path="/mcp",      # Where to mount the MCP server
    name="My API MCP",      # Name for the MCP server
)
```

That's it! Your auto-generated MCP server is now available at `https://app.base.url/mcp`.

## Authentication

FastAPI-MCP supports various authentication methods to secure your MCP server:

### Simple Bearer Token Authentication

```python
from fastapi import FastAPI
from fastapi_mcp import add_mcp_server, AuthConfig

app = FastAPI()

# Configure authentication with a bearer token
auth_config = AuthConfig(
    enabled=True,
    bearer_token="your-secret-token"  # This should be a secure token
)

# Add MCP server with authentication
mcp_server = add_mcp_server(
    app,
    mount_path="/mcp",
    name="Authenticated MCP API",
    auth_config=auth_config
)
```

### API Key Authentication

```python
from fastapi_mcp import AuthConfig

# Configure authentication with an API key in header
auth_config = AuthConfig(
    enabled=True,
    api_key="your-api-key",
    api_key_name="X-API-Key",
    api_key_in="header"  # Can be "header" or "query"
)
```

### Custom Authentication

For more complex authentication scenarios, you can use a custom authentication function:

```python
from fastapi import Request
from fastapi_mcp import AuthConfig

# Define your custom authentication function
async def my_auth_function(request: Request) -> bool:
    # Your authentication logic here
    # Return True if authenticated, False otherwise
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    return token == "valid-token"

# Configure authentication with a custom function
auth_config = AuthConfig(
    enabled=True,
    custom_auth_func=my_auth_function
)
```

See the [examples/authenticated_server.py](examples/authenticated_server.py) and [examples/simple_bearer_auth.py](examples/simple_bearer_auth.py) for complete working examples.

## Advanced Usage

FastAPI-MCP provides several ways to customize and control how your MCP server is created and configured. Here are some advanced usage patterns:

```python
from fastapi import FastAPI
from fastapi_mcp import add_mcp_server

app = FastAPI()

mcp_server = add_mcp_server(
    app,                                    # Your FastAPI app
    mount_path="/mcp",                      # Where to mount the MCP server
    name="My API MCP",                      # Name for the MCP server
    describe_all_responses=True,            # False by default. Include all possible response schemas in tool descriptions, instead of just the successful response.
    describe_full_response_schema=True      # False by default. Include full JSON schema in tool descriptions, instead of just an LLM-friendly response example.
)

# Optionally add custom tools in addition to existing APIs.
@mcp_server.tool()
async def get_server_time() -> str:
    """Get the current server time."""
    from datetime import datetime
    return datetime.now().isoformat()
```

## Examples

See the [examples](examples) directory for complete examples.

## Connecting to the MCP Server using SSE

Once your FastAPI app with MCP integration is running, you can connect to it with any MCP client supporting SSE, such as Cursor:

1. Run your application.

2. In Cursor -> Settings -> MCP, use the URL of your MCP server endpoint (e.g., `http://localhost:8000/mcp`) as sse.

3. Cursor will discover all available tools and resources automatically.

## Connecting to the MCP Server using [mcp-proxy stdio](https://github.com/sparfenyuk/mcp-proxy?tab=readme-ov-file#1-stdio-to-sse) 

If your MCP client does not support SSE, for example Claude Desktop: 

1. Run your application.

2. Install [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy?tab=readme-ov-file#installing-via-pypi), for example: `uv tool install mcp-proxy`.

3. Add in Claude Desktop MCP config file (`claude_desktop_config.json`):

On Windows:
```json
{
  "mcpServers": {
    "my-api-mcp-proxy": {
        "command": "mcp-proxy",
        "args": ["http://127.0.0.1:8000/mcp"]
    }
  }
}
```
On MacOS: 
```json
{
  "mcpServers": {
    "my-api-mcp-proxy": {
        "command": "/Full/Path/To/Your/Executable/mcp-proxy",
        "args": ["http://127.0.0.1:8000/mcp"]
    }
  }
}
```
Find the path to mcp-proxy by running in Terminal: `which mcp-proxy`.

4. Claude Desktop will discover all available tools and resources automatically

## Development and Contributing

If you're interested in contributing to FastAPI-MCP:

```bash
# Clone the repository
git clone https://github.com/tadata-org/fastapi_mcp.git
cd fastapi_mcp

# Create a virtual environment and install dependencies with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv add -e ".[dev]"

# Run tests
uv run pytest
```

For more details about contributing, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Community

Join [MCParty Slack community](https://join.slack.com/t/themcparty/shared_invite/zt-30yxr1zdi-2FG~XjBA0xIgYSYuKe7~Xg) to connect with other MCP enthusiasts, ask questions, and share your experiences with FastAPI-MCP.

## Requirements

- Python 3.10+
- uv

## License

MIT License. Copyright (c) 2024 Tadata Inc.

## About

Developed and maintained by [Tadata Inc.](https://github.com/tadata-org)