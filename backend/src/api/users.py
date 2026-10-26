import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select
from src.api.auth import (
    create_access_token,
    create_refresh_token_in_db,
    get_current_user,
    get_password_hash,
    verify_password,
)
from src.lib.database import get_session
from src.models.user import User

logger = logging.getLogger("todo-api")

router = APIRouter(prefix="/users", tags=["users"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str  # Will be hashed


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool
    created_at: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: Session = Depends(get_session),
):
    """Authenticate user and return JWT access token and refresh token."""
    try:
        user = session.exec(select(User).where(User.email == request.email)).first()

        if not user:
            logger.warning(f"Login failed - user not found: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not verify_password(request.password, user.hashed_password):
            logger.warning(f"Login failed - invalid password for: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        if not user.is_active:
            logger.warning(f"Login failed - user inactive: {request.email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Create access token (short-lived: 15 minutes)
        access_token = create_access_token(data={"sub": str(user.id)})

        # Create refresh token (long-lived: 30 days)
        refresh_token, _ = create_refresh_token_in_db(
            session=session,
            user_id=user.id,
        )

        logger.info(f"User {user.id} logged in successfully")
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login",
        ) from e


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    request: RegisterRequest,
    session: Session = Depends(get_session),
):
    """Register a new user account."""
    try:
        # Check if email already exists
        existing_email = session.exec(
            select(User).where(User.email == request.email)
        ).first()

        if existing_email:
            logger.warning(
                f"Registration failed - email already exists: {request.email}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        # Check if username already exists
        existing_username = session.exec(
            select(User).where(User.username == request.username)
        ).first()

        if existing_username:
            logger.warning(
                f"Registration failed - username already exists: {request.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )

        # Create new user
        user = User(
            username=request.username,
            email=request.email,
            hashed_password=get_password_hash(request.password),
            is_active=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        logger.info(f"New user registered: {user.id}")
        return UserResponse(
            id=str(user.id),
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration",
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user profile."""
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
    )
