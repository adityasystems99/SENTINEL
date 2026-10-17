"""Server-enforced authentication, authorization, and workspace isolation.
Cryptographically signs and validates user identity to eliminate user impersonation.
"""
import hashlib
import hmac
import time
from typing import Optional
from fastapi import Header, HTTPException, status
from pydantic import BaseModel
from ..config import settings
from ..models.project import ProjectMetadata


class UserContext(BaseModel):
    user_id: str
    role: str = "user"  # "user" | "admin"


def create_signed_token(user_id: str, role: str = "user", ttl_seconds: int = 86400) -> str:
    """Create a tamper-proof cryptographically signed access token.
    Format: <user_id>.<role>.<expiry_timestamp>.<hmac_signature>
    """
    clean_user = user_id.strip()
    clean_role = role.strip()
    expiry = int(time.time()) + ttl_seconds
    payload = f"{clean_user}:{clean_role}:{expiry}"
    sig = hmac.new(settings.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_signed_token(token: str) -> Optional[UserContext]:
    """Validate a cryptographically signed access token.
    Returns UserContext if signature is valid and token is unexpired; None otherwise.
    """
    parts = token.split(":")
    if len(parts) != 4:
        return None

    user_id, role, expiry_str, provided_sig = parts
    try:
        expiry = int(expiry_str)
    except ValueError:
        return None

    if time.time() > expiry:
        return None

    payload = f"{user_id}:{role}:{expiry}"
    expected_sig = hmac.new(settings.secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(provided_sig, expected_sig):
        return None

    if role not in ("user", "admin"):
        return None

    return UserContext(user_id=user_id, role=role)


async def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> UserContext:
    """Validate incoming client credentials and resolve to authenticated UserContext.
    
    Rejects any unverified, forged, or spoofed identity claims.
    Supports:
    - Authorization: Bearer <signed_token | api_key>
    - X-API-Key: <api_key>
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
        # Permissive development mode without auth header
        return UserContext(user_id="demo_user", role="user")

    # 1. Validate against configured pre-shared server keys
    if token == settings.admin_api_key:
        return UserContext(user_id="admin_user", role="admin")

    if token == settings.api_key:
        return UserContext(user_id="demo_user", role="user")

    # 2. Validate against server-signed cryptographic token
    signed_user = verify_signed_token(token)
    if signed_user:
        return signed_user

    # 3. Reject invalid / forged credentials
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
