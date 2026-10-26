from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship


def utcnow():
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class OAuthAccount(SQLModel, table=True):
    """OAuth account linking for social login (Google, GitHub, etc.).

    Links a user account to one or more OAuth providers. Allows users to:
    - Sign in with Google, GitHub, etc.
    - Link multiple OAuth providers to one account
    - Have both password auth AND OAuth (hybrid)

    Security notes:
    - Store OAuth provider's access tokens (encrypted in production)
    - provider_user_id is the unique ID from the OAuth provider
    - One user can have multiple OAuth accounts (Google + GitHub)
    - One OAuth account links to exactly one user
    """

    __tablename__: str = "oauth_account"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)

    # OAuth Provider Info
    provider: str = Field(index=True)  # "google", "github", "microsoft", etc.
    provider_user_id: str = Field(index=True)  # User ID from the provider
    provider_email: Optional[str] = Field(
        default=None
    )  # Email from provider (for linking)

    # OAuth Tokens (store for API access on behalf of user)
    access_token: Optional[str] = Field(default=None)  # OAuth access token
    refresh_token: Optional[str] = Field(
        default=None
    )  # OAuth refresh token (if provided)
    token_expires_at: Optional[datetime] = Field(
        default=None
    )  # When OAuth token expires

    # Metadata
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    # Unique constraint: one user can't link the same OAuth account twice
    # This is enforced at the database level in the migration
