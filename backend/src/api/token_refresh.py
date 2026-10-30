import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session
from src.api.auth import (
    create_access_token,
    create_refresh_token_in_db,
    get_current_user,
    revoke_all_user_tokens,
    revoke_refresh_token,
    verify_refresh_token,
)
from src.lib.database import get_session
from src.models.user import User

logger = logging.getLogger("todo-api")

router = APIRouter(prefix="/auth", tags=["authentication"])


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    message: str


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: RefreshRequest,
    session: Session = Depends(get_session),
    user_agent: Optional[str] = Header(None),
):
    """Exchange a valid refresh token for a new access token and refresh token.

    This implements token rotation for enhanced security:
    - Old refresh token is revoked
    - New refresh token is issued
    - New short-lived access token is issued

    Returns:
        TokenResponse with new access_token and refresh_token
    """
    # Verify the refresh token
    user = verify_refresh_token(session, request.refresh_token)
    if not user:
        logger.warning("Invalid or expired refresh token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the old refresh token (token rotation)
    revoke_refresh_token(session, request.refresh_token)

    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Create new refresh token (rotation)
    new_refresh_token, _ = create_refresh_token_in_db(
        session=session,
        user_id=user.id,
        user_agent=user_agent,
    )

    logger.info(f"Token refreshed for user {user.id}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: RefreshRequest,
    session: Session = Depends(get_session),
):
    """Logout by revoking a specific refresh token.

    This logs out the current device/session only.
    To logout all devices, use /auth/logout-all instead.
    """
    success = revoke_refresh_token(session, request.refresh_token)

    if not success:
        # Don't reveal whether token exists for security
        pass

    logger.info("User logged out (single device)")
    return MessageResponse(message="Logged out successfully")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all_devices(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Logout from all devices by revoking all refresh tokens for the current user.

    Requires a valid access token to identify the user.
    """
    count = revoke_all_user_tokens(session, current_user.id)

    logger.info(
        f"User {current_user.id} logged out from all devices ({count} tokens revoked)"
    )
    return MessageResponse(message=f"Logged out from {count} device(s)")
