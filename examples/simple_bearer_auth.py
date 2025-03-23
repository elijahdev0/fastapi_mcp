"""
Example of a FastAPI-MCP server with simple bearer token authentication.

This example demonstrates how to add simple bearer token authentication to an MCP server.
"""

from fastapi import FastAPI, Depends, HTTPException, Header
from typing import List, Dict, Optional

from fastapi_mcp import add_mcp_server, AuthConfig

# Create FastAPI app
app = FastAPI(
    title="Simple Bearer Auth MCP Example",
    description="An example of an MCP server with simple bearer token authentication",
)

# Define a fixed API token for simplicity
# In a real application, this should be stored securely
API_TOKEN = "mcp-test-token-123456"


# Helper function to verify the token in regular FastAPI endpoints
async def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization.replace("Bearer ", "")
    if token != API_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


# Sample items database
items_db: Dict[str, dict] = {
    "1": {"id": "1", "name": "Foo", "description": "This is foo"},
    "2": {"id": "2", "name": "Bar", "description": "This is bar"},
    "3": {"id": "3", "name": "Baz", "description": "This is baz"},
}


@app.get("/items/", response_model=List[dict])
async def read_items(token: str = Depends(verify_token)):
    """Get all items, requires authentication."""
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=dict)
async def read_item(item_id: str, token: str = Depends(verify_token)):
    """Get a specific item, requires authentication."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


# Add MCP server with authentication using a simple bearer token
auth_config = AuthConfig(
    enabled=True,
    bearer_token=API_TOKEN  # Directly use the API token for bearer auth
)

mcp_server = add_mcp_server(
    app,
    mount_path="/mcp",
    name="Bearer Auth MCP API",
    description="MCP server with simple bearer token authentication",
    base_url="http://localhost:8000",
    auth_config=auth_config
)


# Add a custom MCP tool
@mcp_server.tool()
async def get_item_count() -> int:
    """Get the total number of items in the database."""
    return len(items_db)


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with bearer token authentication. Use token: {API_TOKEN}")
    print("Example: curl -H 'Authorization: Bearer mcp-test-token-123456' http://localhost:8000/items/")
    print("For MCP: Use the same Authorization header when connecting to /mcp")
    uvicorn.run(app, host="127.0.0.1", port=8000)