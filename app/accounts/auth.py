"""Accounts Auth"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Header
from tortoise.exceptions import OperationalError

from app.config.settings import settings
from app.accounts.models import Account
from app.base.utils import IDPrefix

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
REFRESH_TOKEN_EXPIRE_DAYS = 90
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 6

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using Argon2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "scope": "access_token"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {**data, "exp": expire, "scope": "refresh_token"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived JWT used only to complete a password reset after OTP."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    )
    to_encode = {**data, "exp": expire, "scope": "password_reset"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_admin_password_setup_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a short-lived JWT exchanged from an opaque admin setup code."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    )
    to_encode = {**data, "exp": expire, "scope": "admin_password_setup"}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode a JWT and validate its signature."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_refresh_token(token: str) -> dict:
    """Decode a JWT refresh token and validate its signature and scope."""
    payload = decode_token(token)
    if payload.get("scope") != "refresh_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token scope",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


_RESET_SCOPES = frozenset({"password_reset", "admin_password_setup"})


def decode_password_reset_token(token: str) -> dict:
    """Decode a password-reset JWT and validate its scope."""
    payload = decode_token(token)
    if payload.get("scope") not in _RESET_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token scope",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_user_from_token(token: str) -> Optional[Account]:
    """Retrieve a user object from a JWT token with DB error handling."""
    payload = decode_token(token)
    if payload.get("scope") != "access_token":
        raise HTTPException(status_code=401, detail="Invalid token scope")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing user ID in token")

    if not user_id.startswith(f"{IDPrefix.ACCOUNT}_"):
        raise HTTPException(status_code=401, detail="Invalid user ID format")

    try:
        user = await Account.filter(id=user_id).first()
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    if "v" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token version")
    token_v = int(payload["v"])
    if token_v != user.auth_token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
        )

    token_pv = int(payload.get("pv", 0))
    if token_pv != int(user.permissions_version):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or revoked",
        )

    return user


def _bearer_token_from_authorization(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() in {"bearer", "jwt"}:
        return parts[1]
    return None


async def get_user_from_password_reset_token(
    authorization: Optional[str] = Header(None),
) -> Account:
    """Load the account for a valid password-reset JWT from Authorization header."""
    token = _bearer_token_from_authorization(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_password_reset_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing user ID in token",
        )
    if not str(user_id).startswith(f"{IDPrefix.ACCOUNT}_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
        )
    try:
        user = await Account.filter(id=user_id).first()
    except OperationalError:
        raise HTTPException(status_code=500, detail="Database connection error") from None
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error") from None
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if "v" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid reset token",
        )
    if int(payload.get("v")) != user.auth_token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset session",
        )
    return user


async def get_current_user(authorization: Optional[str] = Header(None)) -> Account:
    """Resolve current user from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = _bearer_token_from_authorization(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    return await get_user_from_token(token)


async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Account]:
    """Resolve current user from Authorization header, returns None if not authenticated."""
    if not authorization:
        return None

    token = _bearer_token_from_authorization(authorization)
    if not token:
        return None

    try:
        return await get_user_from_token(token)
    except HTTPException:
        return None
