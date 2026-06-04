"""
Security module for handling password hashing, authentication, and JWT token management
"""

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

__all__ = ["verify_password", "hash_password", "pwd_context", "create_access_token", "verify_access_token"]

# Work factor for the hashing algorithm
BCRYPT_ROUNDS = 12

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely compares a raw password with a hashed password using the configured hashing algorithm
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Generates a secure hash of the given plain text password
    """
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """
    Creates a signed JWT access token with an expiration time
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_access_token(token: str) -> dict:
    """
    Verifies and decodes a JWT token. Raises an exception if invalid or expired
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])