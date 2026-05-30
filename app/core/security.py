"""
Security module for handling password hashing, authentication, and future JWT token management
"""

from passlib.context import CryptContext

__all__ = ["verify_password", "hash_password", "pwd_context"]

# Work factor for the hashing algorithm
BCRYPT_ROUNDS = 12  # 12 rounds is a good balance between security and performance for most applications.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=BCRYPT_ROUNDS)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Safely compares a raw password with a hashed password using the configured hashing algorithm
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Generates a secure hash of the given plain text password using the configured hashing algorithm and work factor
    """
    return pwd_context.hash(password)


# TODO: Implement JWT token generation and verification functions for future authentication features
