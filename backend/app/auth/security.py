"""Server-enforced authentication, authorization, and workspace isolation."""
from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from ..config import settings
from ..models.project import ProjectMetadata


class UserContext(BaseModel):
    user_id: str
    role: str = "user"  # "user" | "admin"


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> UserContext:
    """Validate incoming client credentials and resolve to authenticated UserContext.
    
    Supports:
    - Authorization: Bearer <token>
    - X-API-Key: <token>
    
    Supported tokens:
    - settings.admin_api_key -> admin role
    - settings.api_key -> user role (demo_user)
    - admin:<username> -> admin role
    - user:<username> -> user role (allows scoped multi-user tenant testing)
    """
    token: Optional[str] = None
    if authorization:
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
        elif len(parts) == 1:
            token = parts[0]
    elif x_api_key:
        token = x_api_key.strip()

    # If no credentials provided
    if not token:
        if settings.auth_enabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials required. Supply 'Authorization: Bearer <token>' or 'X-API-Key' header.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Development / permissive mode without auth header
        return UserContext(user_id="demo_user", role="user")

    # Validate provided credentials
    if token == settings.admin_api_key:
        return UserContext(user_id="admin_user", role="admin")

    if token == settings.api_key:
        return UserContext(user_id="demo_user", role="user")

    if token.startswith("admin:"):
        admin_id = token[6:].strip()
        if admin_id:
            return UserContext(user_id=admin_id, role="admin")

    if token.startswith("user:"):
        user_id = token[5:].strip()
        if user_id:
            return UserContext(user_id=user_id, role="user")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def verify_project_ownership(project: ProjectMetadata, user: UserContext) -> None:
    """Enforce workspace tenant isolation.
    
    Admins can access any workspace. Regular users can only access projects they own.
    """
    if user.role == "admin":
        return
    if project.owner_id == user.user_id:
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Forbidden: You do not have permission to access project workspace '{project.project_id}'.",
    )
