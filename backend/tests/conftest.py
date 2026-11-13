"""Ensure the ``app`` package is importable when running ``pytest backend/tests/``."""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from app.core.security import verify_api_key  # noqa: E402
    from app.main import app  # noqa: E402
    HAS_APP = True
except ImportError:
    HAS_APP = False
    verify_api_key = None
    app = None


@pytest.fixture(autouse=True)
def override_api_key():
    """Bypass API-key auth for the existing suite.

    Security-specific tests remove this override explicitly to exercise the
    real ``verify_api_key`` dependency.
    """
    if HAS_APP and app is not None and verify_api_key is not None:
        app.dependency_overrides[verify_api_key] = lambda: "test-valid-key"
        yield
        app.dependency_overrides.pop(verify_api_key, None)
    else:
        yield
