"""Redis-backed cache for computed comparison reports.

Reports are stored as JSON under the key ``comparison:{comparison_id}`` with a
24-hour TTL. When Redis is unreachable (e.g. in unit tests or before the
container is up) the module transparently falls back to an in-memory dict so
that nothing breaks without Redis.
"""

import collections
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

try:
    import redis
except ImportError:
    redis = None

from app.core.config import settings

logger = logging.getLogger(__name__)

DEFAULT_TTL = 86400  # 24 hours, in seconds.
MAX_FALLBACK_ITEMS = 1000
RECONNECT_INTERVAL_SECONDS = 10.0

_client: Optional[Any] = None
_client_initialized = False
_last_connect_attempt = 0.0

#: In-memory fallback used when Redis is not available: key -> (expires_at, payload)
_fallback: collections.OrderedDict[str, Tuple[float, str]] = collections.OrderedDict()


def _redis_client() -> Optional[Any]:
    global _client, _client_initialized, _last_connect_attempt
    now = time.time()
    if _client_initialized and _client is not None:
        return _client
    if _client_initialized and (now - _last_connect_attempt) < RECONNECT_INTERVAL_SECONDS:
        return None

    _client_initialized = True
    _last_connect_attempt = now

    if redis is None:
        logger.debug("Redis package not installed; using in-memory fallback.")
        _client = None
        return _client
    try:
        candidate = redis.Redis.from_url(
            settings.REDIS_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        candidate.ping()
        _client = candidate
        logger.info("Connected to Redis at %s", settings.REDIS_URL)
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

    # In-memory fallback with bounded capacity & TTL
    expires_at = time.time() + ttl
    _fallback[key] = (expires_at, payload)
    _fallback.move_to_end(key)
    while len(_fallback) > MAX_FALLBACK_ITEMS:
        _fallback.popitem(last=False)


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

    entry = _fallback.get(key)
    if entry is None:
        return None

    expires_at, payload = entry
    if time.time() > expires_at:
        del _fallback[key]
        return None

    _fallback.move_to_end(key)
    return json.loads(payload)
