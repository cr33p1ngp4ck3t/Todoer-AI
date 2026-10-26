"""OAuth authentication endpoints for social login (Google, GitHub, etc.)"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from src.lib.oauth_providers import oauth, is_provider_supported
from src.lib.database import get_session
from src.models.user import User
from src.models.oauth_account import OAuthAccount
from src.api.auth import (
    create_access_token,
    create_refresh_token_in_db,
    get_password_hash,
)
from typing import Optional
from datetime import datetime, timezone
import logging
import os

logger = logging.getLogger("todo-api")

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

# Frontend URL for redirecting after OAuth (change for production)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


@router.get("/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login flow.

    Redirects user to the OAuth provider's consent screen.

    Args:
        provider: OAuth provider name ('google', 'github', etc.)

    Returns:
        Redirect to OAuth provider's authorization URL
    """
    if not is_provider_supported(provider):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth provider '{provider}' is not supported",
        )

    # Build redirect URI (this is where OAuth provider sends user back)
    redirect_uri = request.url_for("oauth_callback", provider=provider)

    logger.info(f"Initiating OAuth login for provider: {provider}")

    # Redirect to OAuth provider
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    session: Session = Depends(get_session),
):
    """Handle OAuth callback after user authorizes.

    This endpoint:
    1. Exchanges authorization code for access token
    2. Fetches user info from OAuth provider
    3. Creates or links user account
    4. Returns JWT tokens to frontend

    Args:
        provider: OAuth provider name
        request: FastAPI request object (contains auth code)

    Returns:
        Redirect to frontend with tokens in URL
    """
    if not is_provider_supported(provider):
        logger.warning(f"OAuth callback for unsupported provider: {provider}")
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=unsupported_provider")

    try:
        # Exchange authorization code for access token
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)

        # Get user info from OAuth provider
        if provider == "google":
            user_info = token.get("userinfo")
            if not user_info:
                # Fallback: manually fetch userinfo
                resp = await client.get("https://www.googleapis.com/oauth2/v3/userinfo")
                user_info = resp.json()

            provider_user_id = user_info["sub"]  # Google's user ID
            email = user_info["email"]
            name = user_info.get("name", email.split("@")[0])

        elif provider == "github":
            # GitHub requires separate API call to get user info
            # Pass token explicitly for authenticated requests
            resp = await client.get("https://api.github.com/user", token=token)
            user_info = resp.json()

            provider_user_id = str(user_info["id"])  # GitHub user ID
            email = user_info.get("email")

            # GitHub email might be null if user hasn't made it public
            if not email:
                # Fetch verified emails
                emails_resp = await client.get(
                    "https://api.github.com/user/emails", token=token
                )
                emails = emails_resp.json()
                # Get primary verified email
                for email_data in emails:
                    if email_data["primary"] and email_data["verified"]:
                        email = email_data["email"]
                        break

            if not email:
                raise Exception("Could not fetch verified email from GitHub")

            name = user_info.get("login", email.split("@")[0])

        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")

        logger.info(f"OAuth callback successful for {provider}, email: {email}")

        # Check if OAuth account already exists (returning user)
        existing_oauth = session.exec(
            select(OAuthAccount)
            .where(OAuthAccount.provider == provider)
            .where(OAuthAccount.provider_user_id == provider_user_id)
        ).first()

        if existing_oauth:
            # Returning user - log them in
            user = session.get(User, existing_oauth.user_id)

            if not user or not user.is_active:
                logger.warning(f"OAuth account exists but user inactive: {email}")
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/login?error=account_inactive"
                )

            # Update OAuth token in case it changed
            existing_oauth.access_token = token.get("access_token")
            existing_oauth.refresh_token = token.get("refresh_token")
            # Convert Unix timestamp to datetime if present
            expires_at = token.get("expires_at")
            if expires_at:
                existing_oauth.token_expires_at = datetime.fromtimestamp(
                    expires_at, tz=timezone.utc
                )
            session.commit()

            logger.info(f"Existing user logged in via {provider}: {user.id}")

        else:
            # New user - check if email already exists
            existing_user = session.exec(
                select(User).where(User.email == email)
            ).first()

            if existing_user:
                # User exists with this email - link OAuth account
                user = existing_user
                logger.info(f"Linking {provider} account to existing user: {user.id}")
            else:
                # Brand new user - create account
                user = User(
                    username=name.lower().replace(" ", "_")[:50],  # Sanitize username
                    email=email,
                    hashed_password=get_password_hash(
                        os.urandom(32).hex()
                    ),  # Random password
                    is_active=True,
                )
                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info(f"Created new user via {provider} OAuth: {user.id}")

            # Create OAuth account link
            # Convert Unix timestamp to datetime if present
            expires_at = token.get("expires_at")
            token_expires_at = None
            if expires_at:
                token_expires_at = datetime.fromtimestamp(expires_at, tz=timezone.utc)

            oauth_account = OAuthAccount(
                user_id=user.id,
                provider=provider,
                provider_user_id=provider_user_id,
                provider_email=email,
                access_token=token.get("access_token"),
                refresh_token=token.get("refresh_token"),
                token_expires_at=token_expires_at,
            )
            session.add(oauth_account)
            session.commit()

        # Generate our JWT tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token, _ = create_refresh_token_in_db(
            session=session,
            user_id=user.id,
        )

        # Redirect to frontend with tokens
        # Frontend should extract tokens from URL and store them
        redirect_url = (
            f"{FRONTEND_URL}/auth/callback"
            f"?access_token={access_token}"
            f"&refresh_token={refresh_token}"
            f"&token_type=bearer"
        )

        return RedirectResponse(url=redirect_url)

    except Exception as e:
        logger.error(f"OAuth callback error for {provider}: {str(e)}", exc_info=True)
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=oauth_failed")
