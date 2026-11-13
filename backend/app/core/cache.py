"""Redis-backed cache for computed comparison reports.

Reports are stored as JSON under the key ``comparison:{comparison_id}`` with a
24-hour TTL. When Redis is unreachable (e.g. in unit tests or before the
container is up) the module transparently falls back to an in-memory dict so
that nothing breaks without Redis.
"""

import json
import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400  # 24 hours, in seconds.

_client: Optional[redis.Redis] = None
_client_initialized = False

#: In-memory fallback used when Redis is not available.
_fallback: Dict[str, str] = {}


def _redis_client() -> Optional[redis.Redis]:
    global _client, _client_initialized
    if _client_initialized:
        return _client
    _client_initialized = True
    try:
        _client = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        _client.ping()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Redis unavailable (%s); using in-memory fallback.", exc)
        _client = None
    return _client


def set_report(comparison_id: str, data: Any, ttl: int = DEFAULT_TTL) -> None:
    """Store a report under ``comparison:{comparison_id}`` with the given TTL."""
    key = f"comparison:{comparison_id}"
    payload = json.dumps(data, ensure_ascii=False)

    client = _redis_client()
    if client is not None:
        try:
            client.setex(key, ttl, payload)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis set failed (%s); using in-memory fallback.", exc)

    _fallback[key] = payload


def get_report(comparison_id: str) -> Optional[Any]:
    """Return a previously stored report, or ``None`` if it does not exist."""
    key = f"comparison:{comparison_id}"

    client = _redis_client()
    if client is not None:
        try:
            raw = client.get(key)
            if raw is not None:
                return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis get failed (%s); using in-memory fallback.", exc)

    raw = _fallback.get(key)
    if raw is None:
        return None
    return json.loads(raw)
