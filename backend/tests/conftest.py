"""Ensure the ``app`` package is importable when running ``pytest backend/tests/``."""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import verify_api_key  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def override_api_key():
    """Bypass API-key auth for the existing suite.

    Security-specific tests remove this override explicitly to exercise the
    real ``verify_api_key`` dependency.
    """
    app.dependency_overrides[verify_api_key] = lambda: "test-valid-key"
    yield
    app.dependency_overrides.pop(verify_api_key, None)
