"""
SentinelX Authentication Module
================================
- RS256 asymmetric JWT signing (private key signs, public key verifies)
- bcrypt + pepper password hashing (double-layered)
- Access token (15 min) + Refresh token (7 days)
- FastAPI dependency: get_current_active_user
"""
from __future__ import annotations

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# ── Key material ────────────────────────────────────────────────────────────
# RS256: private key for signing, public key for verification.
# Generate with:  openssl genrsa -out private.pem 4096
#                 openssl rsa -in private.pem -pubout -out public.pem
JWT_PRIVATE_KEY: str = os.environ["JWT_PRIVATE_KEY"]
JWT_PUBLIC_KEY: str = os.environ["JWT_PUBLIC_KEY"]
JWT_ALGORITHM = "RS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# A server-side pepper added before bcrypt (so a DB dump alone can't crack passwords)
PASSWORD_PEPPER: str = os.environ["PASSWORD_PEPPER"]

# ── Password context ─────────────────────────────────────────────────────────
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

bearer_scheme = HTTPBearer(auto_error=True)


def _pepper(plain: str) -> str:
    """Apply HMAC-SHA256 pepper before bcrypt to frustrate offline attacks."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        plain.encode(),
        PASSWORD_PEPPER.encode(),
        iterations=1,
    ).hex()


def get_password_hash(plain: str) -> str:
    return _pwd_context.hash(_pepper(plain))


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(_pepper(plain), hashed)


# ── Token creation ────────────────────────────────────────────────────────────
def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict] = None,
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
        "jti": secrets.token_hex(16),          # unique token ID (for revocation)
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, JWT_PRIVATE_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: int) -> str:
    return _create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises HTTPException on any failure."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception


# ── FastAPI dependencies ──────────────────────────────────────────────────────
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    return current_user


def require_role(required_role: str):
    """Dependency factory: require a specific role (e.g. 'admin')."""
    def _check(user: models.User = Depends(get_current_active_user)) -> models.User:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required",
            )
        return user
    return _check
