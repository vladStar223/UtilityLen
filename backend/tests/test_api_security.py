"""Security regression tests for the API surface (Block 1)."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import verify_api_key
from app.main import app

TEST_API_KEY = "test-secret-key"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def _enable_auth(monkeypatch):
    """Configure a real API key and disable the autouse override."""
    monkeypatch.setattr(settings, "API_KEY", TEST_API_KEY)
    app.dependency_overrides.pop(verify_api_key, None)


# --- B3: API-key authentication -------------------------------------------------


def test_health_is_public_without_key(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_cases_requires_api_key(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.get("/api/v1/cases")
    assert resp.status_code == 401


def test_cases_with_valid_api_key(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.get("/api/v1/cases", headers={"X-API-Key": TEST_API_KEY})
    assert resp.status_code == 200
    assert "cases" in resp.json()


def test_cases_with_invalid_api_key(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.get("/api/v1/cases", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


# --- B1: Path traversal protection in case_id -----------------------------------


@pytest.mark.parametrize(
    "evil_case_id",
    [
        "../../etc",
        "../data/cases/case_02_coeff_15",
        "../../../../etc/passwd",
    ],
)
def test_compare_rejects_path_traversal_case_id(client, monkeypatch, evil_case_id):
    _enable_auth(monkeypatch)
    resp = client.post(
        "/api/v1/compare",
        json={"case_id": evil_case_id},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code in (400, 404, 422), resp.text


def test_compare_legitimate_case_id(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.post(
        "/api/v1/compare",
        json={"case_id": "case_02_coeff_15"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["comparison_id"].startswith("cmp-")


# --- B5: CORS preflight ---------------------------------------------------------


def test_cors_preflight_allows_configured_origin(client):
    origin = "http://localhost:8501"
    resp = client.options(
        "/api/v1/cases",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, X-API-Key",
        },
    )
    assert resp.status_code == 200
    assert resp.headers["access-control-allow-origin"] == origin
    assert "GET" in resp.headers["access-control-allow-methods"]
    assert "X-API-Key" in resp.headers["access-control-allow-headers"]
    assert "authorization" in resp.headers["access-control-allow-headers"].lower()


def test_cors_preflight_rejects_unknown_origin(client):
    resp = client.options(
        "/api/v1/cases",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 400
    assert "access-control-allow-origin" not in resp.headers


# --- B7: request size limits (HTTP 422) ---------------------------------------


def _minimal_bill(raw_name: str = "Холодное водоснабжение") -> dict:
    return {
        "bill_id": "bill-001",
        "period": "2024-01",
        "address": "г. Владивосток",
        "total_amount": 100.0,
        "services": [
            {
                "service_code": "cold_water",
                "raw_name": raw_name,
                "unit": "м3",
                "volume": 1.0,
                "tariff": 10.0,
                "total": 10.0,
            }
        ],
    }


def test_compare_rejects_oversized_raw_name(client):
    resp = client.post(
        "/api/v1/compare",
        json={
            "prev_bill": _minimal_bill("x" * 501),
            "curr_bill": _minimal_bill("ok"),
        },
    )
    assert resp.status_code == 422


def test_chat_rejects_oversized_message(client):
    resp = client.post(
        "/api/v1/chat/stream",
        json={"comparison_id": "cmp-test", "message": "x" * 2001},
    )
    assert resp.status_code == 422


def test_chat_rejects_oversized_history(client):
    resp = client.post(
        "/api/v1/chat/stream",
        json={
            "comparison_id": "cmp-test",
            "message": "hello",
            "history": [{"role": "user", "content": "m"}] * 51,
        },
    )
    assert resp.status_code == 422


# --- B4: crypto comparison_id ---------------------------------------------------


def test_compare_returns_crypto_comparison_id(client, monkeypatch):
    _enable_auth(monkeypatch)
    resp = client.post(
        "/api/v1/compare",
        json={"case_id": "case_02_coeff_15"},
        headers={"X-API-Key": TEST_API_KEY},
    )
    assert resp.status_code == 200
    import re

    assert re.fullmatch(r"cmp-[0-9a-f]{32}", resp.json()["comparison_id"])
