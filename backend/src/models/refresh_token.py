from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)

def refresh_token_expires():
    """Return expiration time for refresh token (30 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=30)

class RefreshToken(SQLModel, table=True):
    """Refresh token for JWT token rotation.

    Refresh tokens are long-lived tokens (30 days) used to obtain new
    short-lived access tokens (15 minutes) without requiring the user
    to log in again.

    Security notes:
    - Tokens are hashed before storage (never stored in plain text)
    - Tokens can be revoked by setting revoked=True
    - Expired tokens should be cleaned up periodically
    - One user can have multiple active refresh tokens (multiple devices)
    """
    __tablename__: str = "refresh_token"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    token_hash: str = Field(index=True)  # SHA256 hash of the token
    expires_at: datetime = Field(default_factory=refresh_token_expires, index=True)
    created_at: datetime = Field(default_factory=utcnow)
    revoked: bool = Field(default=False, index=True)

    # Optional: Track device/client info for security
    user_agent: Optional[str] = Field(default=None, max_length=500)
    ip_address: Optional[str] = Field(default=None, max_length=45)  # IPv6 max length
