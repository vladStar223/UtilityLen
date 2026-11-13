"""Authentication utilities: password hashing, JWT tokens, and user dependency.

Uses standard Python libraries (hashlib, hmac, base64, json, secrets) for
portable, zero-dependency password hashing (PBKDF2-HMAC-SHA256) and JWT tokens
(RFC 7519 HMAC-SHA256).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from app.core.config import settings
from app.db.database import get_db

try:
    from fastapi import Depends, HTTPException, Security, status
    from fastapi.security import OAuth2PasswordBearer
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
except ImportError:
    # Graceful fallback for environments where FastAPI is not installed (e.g. host python)
    def Depends(dependency=None):  # type: ignore
        return dependency

    def Security(dependency=None, scopes=None):  # type: ignore
        return dependency

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: Any = None, headers: Optional[dict] = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class _Status:
        HTTP_401_UNAUTHORIZED = 401
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404

    status = _Status()  # type: ignore
    oauth2_scheme = None  # type: ignore


SECRET_KEY = getattr(settings, "SECRET_KEY", None) or os.getenv(
    "SECRET_KEY", "utilitylens-jwt-secret-key-production-change-2026"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations and salt."""
    salt = secrets.token_hex(16)
    iterations = 100_000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2_sha256${iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored PBKDF2-HMAC-SHA256 hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations = int(parts[1])
            salt = parts[2]
            stored_hash = parts[3]
            derived = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            return hmac.compare_digest(derived.hex(), stored_hash)
        # Fallback to simple salt$hash format
        if "$" in hashed_password:
            salt, stored_hash = hashed_password.split("$", 1)
            derived = hashlib.sha256((salt + plain_password).encode("utf-8")).hexdigest()
            return hmac.compare_digest(derived, stored_hash)
        return False
    except Exception:
        return False


def _b64_url_encode(data: bytes) -> str:
    """URL-safe base64 encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_url_decode(data_str: str) -> bytes:
    """URL-safe base64 decoding with padding restoration."""
    padding = "=" * ((4 - len(data_str) % 4) % 4)
    return base64.urlsafe_b64decode((data_str + padding).encode("ascii"))


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT token (RFC 7519 HMAC-SHA256)."""
    payload = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload["exp"] = int(expire.timestamp())
    payload["iat"] = int(now.timestamp())

    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64_url_encode(header_json)
    payload_b64 = _b64_url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()
    sig_b64 = _b64_url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a signed JWT token. Returns payload dict or None."""
    if not token or not isinstance(token, str):
        return None
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(
            SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()
        actual_sig = _b64_url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64_url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Verify expiration
        exp = payload.get("exp")
        if exp is not None:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            if now_ts > exp:
                return None

        return payload
    except Exception:
        return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Any = Depends(get_db),
) -> Any:
    """FastAPI dependency to extract and authenticate current user from Bearer token."""
    from app.db import crud

    # Strip 'Bearer ' if caller passed full header
    if token and isinstance(token, str) and token.startswith("Bearer "):
        token = token[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истёкший токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит идентификатор пользователя",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = crud.get_user_by_user_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Any = Depends(get_db),
) -> Optional[Any]:
    """Return authenticated user or fallback to demo user if unauthenticated."""
    from app.db import crud

    try:
        if token:
            return get_current_user(token=token, db=db)
    except Exception:
        pass

    # Fallback to demo user if available, otherwise None
    return crud.get_user_by_email(db, "demo@utilitylens.ru")
