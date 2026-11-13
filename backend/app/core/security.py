"""API authentication helpers (API key as MVP).

When ``settings.API_KEY`` is empty the endpoints stay open (handy for local
development and for the existing test suite). As soon as a key is configured,
every protected route requires the ``X-API-Key`` header to match exactly,
using a constant-time comparison to avoid timing side channels.
"""

import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """Validate the ``X-API-Key`` header when a key is configured."""
    expected_key = settings.API_KEY.strip()
    if expected_key:
        if not api_key or not secrets.compare_digest(api_key, expected_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    return api_key or "anonymous"
