"""
Authentication module for FastAPI-MCP.

This module provides functionality for adding authentication to MCP servers in FastAPI applications.
"""

from typing import Optional, Callable, Dict, Any, Union
from fastapi import Request, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader, APIKeyQuery
from pydantic import BaseModel


class AuthConfig(BaseModel):
    """Configuration for MCP authentication."""
    enabled: bool = True
    bearer_token: Optional[str] = None
    api_key: Optional[str] = None
    api_key_name: str = "X-API-Key"
    api_key_in: str = "header"  # "header" or "query"
    custom_auth_func: Optional[Callable[[Request], bool]] = None


class MCPAuthenticator:
    """Class to handle authentication for MCP connections."""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        
        # Set up the security schemes based on configuration
        if self.config.api_key and self.config.api_key_in == "header":
            self.api_key_header = APIKeyHeader(name=self.config.api_key_name, auto_error=False)
        elif self.config.api_key and self.config.api_key_in == "query":
            self.api_key_query = APIKeyQuery(name=self.config.api_key_name, auto_error=False)
        
        if self.config.bearer_token:
            self.http_bearer = HTTPBearer(auto_error=False)
    
    async def authenticate_request(self, request: Request) -> bool:
        """
        Authenticate an incoming request against configured auth methods.
        Returns True if authentication succeeds, False otherwise.
        """
        if not self.config.enabled:
            return True
            
        # Check bearer token if configured
        if self.config.bearer_token:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")
                if token == self.config.bearer_token:
                    return True
        
        # Check API key if configured
        if self.config.api_key:
            if self.config.api_key_in == "header":
                api_key = request.headers.get(self.config.api_key_name)
                if api_key and api_key == self.config.api_key:
                    return True
            elif self.config.api_key_in == "query":
                api_key = request.query_params.get(self.config.api_key_name)
                if api_key and api_key == self.config.api_key:
                    return True
        
        # Use custom auth function if provided
        if self.config.custom_auth_func:
            try:
                return await self.config.custom_auth_func(request)
            except Exception:
                return False
                
        # If we get here, authentication failed
        return False

    async def authenticate_or_raise(self, request: Request) -> None:
        """Authenticate request or raise HTTP 401 exception."""
        if not await self.authenticate_request(request):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Dependencies for use with FastAPI routes
    async def verify_bearer_token(
        self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
    ) -> str:
        """Verify bearer token for FastAPI dependency injection."""
        if not self.config.enabled:
            return "authenticated"
            
        if not self.config.bearer_token:
            raise HTTPException(
                status_code=500,
                detail="Bearer token authentication not configured",
            )
            
        if credentials.credentials != self.config.bearer_token:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials
    
    async def verify_api_key_header(
        self, api_key: str = Security(APIKeyHeader(name="X-API-Key"))
    ) -> str:
        """Verify API key in header for FastAPI dependency injection."""
        if not self.config.enabled:
            return "authenticated"
            
        if not self.config.api_key:
            raise HTTPException(
                status_code=500, 
                detail="API key authentication not configured"
            )
            
        if api_key != self.config.api_key:
            raise HTTPException(
                status_code=401, 
                detail="Invalid API Key"
            )
        return api_key
    
    async def verify_api_key_query(
        self, api_key: str = Security(APIKeyQuery(name="api_key"))
    ) -> str:
        """Verify API key in query for FastAPI dependency injection."""
        if not self.config.enabled:
            return "authenticated"
            
        if not self.config.api_key:
            raise HTTPException(
                status_code=500, 
                detail="API key authentication not configured"
            )
            
        if api_key != self.config.api_key:
            raise HTTPException(
                status_code=401, 
                detail="Invalid API Key"
            )
        return api_key

# Function to create an auth dependency from various authentication options
def create_auth_dependency(
    auth_config: Union[AuthConfig, Dict[str, Any]]
) -> Callable:
    """Create a FastAPI dependency for authentication based on the provided config."""
    
    # Convert dict to AuthConfig if needed
    if isinstance(auth_config, dict):
        auth_config = AuthConfig(**auth_config)
    
    authenticator = MCPAuthenticator(auth_config)
    
    async def auth_dependency(request: Request) -> None:
        """FastAPI dependency for authentication."""
        await authenticator.authenticate_or_raise(request)
    
    return auth_dependency