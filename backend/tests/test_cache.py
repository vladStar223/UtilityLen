"""Tests for the Redis-backed report cache and its in-memory fallback."""

from app.core import cache


def _reset_cache(monkeypatch):
    cache._client = None
    cache._client_initialized = False
    cache._fallback.clear()


class _FakeRedis:
    """Minimal stand-in for a ``redis.Redis`` client."""

    def __init__(self):
        self.store = {}

    def setex(self, key, ttl, value):
        self.store[key] = (ttl, value)

    def get(self, key):
        item = self.store.get(key)
        return item[1] if item else None


def test_fallback_roundtrip(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(cache, "_redis_client", lambda: None)

    cache.set_report("cmp_1", {"delta_abs": 320.25})
    assert cache.get_report("cmp_1") == {"delta_abs": 320.25}


def test_fallback_missing_returns_none(monkeypatch):
    _reset_cache(monkeypatch)
    monkeypatch.setattr(cache, "_redis_client", lambda: None)

    assert cache.get_report("does-not-exist") is None


def test_redis_key_format_and_ttl(monkeypatch):
    _reset_cache(monkeypatch)
    fake = _FakeRedis()
    monkeypatch.setattr(cache, "_redis_client", lambda: fake)

    cache.set_report("cmp_2026_10_11", {"x": 1}, ttl=86400)

    ttl, value = fake.store["comparison:cmp_2026_10_11"]
    assert ttl == 86400
    assert cache.get_report("cmp_2026_10_11") == {"x": 1}


def test_redis_json_roundtrip(monkeypatch):
    _reset_cache(monkeypatch)
    fake = _FakeRedis()
    monkeypatch.setattr(cache, "_redis_client", lambda: fake)

    payload = {
        "report": {"comparison_id": "cmp_1", "summary": {"delta_abs": 1470.5}},
        "curr_bill": {"bill_id": "bill_2026_11_001"},
        "prev_bill": {"bill_id": "bill_2026_10_001"},
    }
    cache.set_report("cmp_1", payload)
    assert cache.get_report("cmp_1") == payload
