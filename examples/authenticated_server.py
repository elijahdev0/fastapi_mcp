"""
Example of a FastAPI-MCP server with authentication.

This example demonstrates how to add authentication to an MCP server.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import jwt
from jwt.exceptions import PyJWTError

from fastapi_mcp import add_mcp_server, AuthConfig

# Create FastAPI app
app = FastAPI(
    title="Authenticated MCP Example",
    description="An example of an MCP server with authentication",
)

# Secret key for JWT token
SECRET_KEY = "a_very_secret_key_that_should_be_changed_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Fake users database
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "john@example.com",
        "hashed_password": "fakehashedsecret",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderland",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": False,
    },
}

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password, hashed_password):
    """Verify password."""
    # This is a fake hash verification - in a real app, use proper hashing
    return plain_password == "secret" and hashed_password == "fakehashedsecret"


def get_user(db, username: str):
    """Get user from the database."""
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    """Authenticate a user."""
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get the current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get an access token."""
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


# Sample items for a simple API
items_db: Dict[str, dict] = {
    "1": {"id": "1", "name": "Foo", "description": "This is foo"},
    "2": {"id": "2", "name": "Bar", "description": "This is bar"},
    "3": {"id": "3", "name": "Baz", "description": "This is baz"},
}


@app.get("/items/", response_model=List[dict])
async def read_items(current_user: User = Depends(get_current_active_user)):
    """Get all items, requires authentication."""
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=dict)
async def read_item(item_id: str, current_user: User = Depends(get_current_active_user)):
    """Get a specific item, requires authentication."""
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


# Function to verify JWT tokens for MCP authentication
async def authenticate_mcp_request(request):
    """Custom authentication function for MCP server."""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return False
        
        token = auth_header.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        
        # Verify user exists in database
        if not username or username not in fake_users_db:
            return False
            
        # Check if user is disabled
        if fake_users_db[username].get("disabled", False):
            return False
            
        return True
    except Exception:
        return False


# Add MCP server with authentication
auth_config = AuthConfig(
    enabled=True,
    # Define a custom auth function that validates JWT tokens
    custom_auth_func=authenticate_mcp_request
)

mcp_server = add_mcp_server(
    app,
    mount_path="/mcp",
    name="Authenticated MCP API",
    description="MCP server with JWT authentication",
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
    uvicorn.run(app, host="127.0.0.1", port=8000)