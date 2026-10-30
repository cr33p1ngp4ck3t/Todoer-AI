import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey
from passlib.context import CryptContext
from sqlmodel import Session, select
from src.lib.database import get_session
from src.models.refresh_token import RefreshToken
from src.models.user import User

# Password hashing context - using argon2 for security and compatibility
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],  # argon2 for new, bcrypt for migration
    deprecated=["bcrypt"],  # Mark bcrypt as deprecated
    argon2__memory_cost=65536,  # 64 MB
    argon2__time_cost=3,  # 3 iterations
    argon2__parallelism=4,  # 4 parallel threads
)

# JWT Configuration (read from environment variables)
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
if not SECRET_KEY:
    raise RuntimeError("Set SECRET_KEY to a random secret before starting the API")
JWT_KEY = OctKey.import_key(SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
)  # Reduced to 15 minutes with refresh tokens
REFRESH_TOKEN_EXPIRE_DAYS = 30  # Refresh tokens last 30 days

security = HTTPBearer()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
    session: Session = Depends(get_session),
) -> User:
    """Extract and validate the authenticated user from a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise credentials_exception
    try:
        token = jwt.decode(credentials.credentials, JWT_KEY, algorithms=[ALGORITHM])
        jwt.JWTClaimsRegistry().validate(token.claims)
        user_id = UUID(token.claims.get("sub", ""))
    except (JoseError, ValueError, TypeError) as exc:
        raise credentials_exception from exc

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode({"alg": ALGORITHM}, to_encode, JWT_KEY, [ALGORITHM])
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Check if password hash needs upgrade to current scheme."""
    return pwd_context.needs_update(hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token.

    Returns a 64-character hex string (32 bytes of randomness).
    """
    return secrets.token_hex(32)


def hash_token(token: str) -> str:
    """Hash a refresh token for storage using SHA-256.

    We hash tokens before storing them so that if the database is compromised,
    the attacker cannot use the tokens directly.
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token_in_db(
    session: Session,
    user_id: UUID,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> tuple[str, "RefreshToken"]:
    """Create a refresh token for a user and store it in the database.

    Returns:
        tuple: (plain_token, refresh_token_model)
            - plain_token: The unhashed token to return to the client
            - refresh_token_model: The database model with hashed token
    """

    from src.models.refresh_token import RefreshToken

    # Generate the plain token
    plain_token = generate_refresh_token()

    # Hash it for storage
    token_hash = hash_token(plain_token)

    # Create database record
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        user_agent=user_agent[:500] if user_agent else None,  # Truncate to max length
        ip_address=ip_address,
    )

    session.add(refresh_token)
    session.commit()
    session.refresh(refresh_token)

    return plain_token, refresh_token


def verify_refresh_token(session: Session, token: str) -> Optional[User]:
    """Verify a refresh token and return the associated user.

    Args:
        session: Database session
        token: The plain refresh token from the client

    Returns:
        User object if token is valid, None otherwise

    Checks:
        1. Token hash exists in database
        2. Token is not revoked
        3. Token is not expired
        4. Associated user exists and is active
    """
    from src.models.refresh_token import RefreshToken

    token_hash = hash_token(token)

    # Find the refresh token
    refresh_token = session.exec(
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .where(RefreshToken.revoked == False)  # noqa: E712
    ).first()

    if not refresh_token:
        return None

    # Check if expired
    if datetime.now(timezone.utc) > refresh_token.expires_at:
        return None

    # Get and return the user
    user = session.get(User, refresh_token.user_id)
    if not user or not user.is_active:
        return None

    return user


def revoke_refresh_token(session: Session, token: str) -> bool:
    """Revoke a refresh token (logout).

    Returns:
        bool: True if token was found and revoked, False otherwise
    """
    from src.models.refresh_token import RefreshToken

    token_hash = hash_token(token)

    refresh_token = session.exec(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    ).first()

    if refresh_token:
        refresh_token.revoked = True
        session.commit()
        return True

    return False


def revoke_all_user_tokens(session: Session, user_id: UUID) -> int:
    """Revoke all refresh tokens for a user (logout all devices).

    Returns:
        int: Number of tokens revoked
    """
    from src.models.refresh_token import RefreshToken

    tokens = session.exec(
        select(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.revoked == False)  # noqa: E712
    ).all()

    count = 0
    for token in tokens:
        token.revoked = True
        count += 1

    session.commit()
    return count
