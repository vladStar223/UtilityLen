"""Tests for authentication logic, password hashing, JWT tokens, and user DB models."""

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import auth
from app.db import crud, models
from app.db.database import Base


@pytest.fixture()
def db():
    """Isolated in-memory SQLite database session."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


# =============================================================================
# Password Hashing Tests
# =============================================================================

def test_password_hashing_and_verification():
    raw_password = "my_secure_password_2026!"
    hashed = auth.hash_password(raw_password)

    assert hashed.startswith("pbkdf2_sha256$100000$")
    assert auth.verify_password(raw_password, hashed) is True
    assert auth.verify_password("wrong_password", hashed) is False
    assert auth.verify_password("", hashed) is False
    assert auth.verify_password(raw_password, "") is False
    assert auth.verify_password(raw_password, "invalid_format") is False


def test_password_salts_are_unique():
    raw_password = "same_password"
    hash1 = auth.hash_password(raw_password)
    hash2 = auth.hash_password(raw_password)

    assert hash1 != hash2
    assert auth.verify_password(raw_password, hash1) is True
    assert auth.verify_password(raw_password, hash2) is True


# =============================================================================
# JWT Token Tests
# =============================================================================

def test_access_token_creation_and_decoding():
    data = {
        "sub": "user_abc123",
        "username": "ivan_ivanov",
        "email": "ivan@example.ru",
    }
    token = auth.create_access_token(data=data, expires_delta=timedelta(minutes=30))

    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    payload = auth.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user_abc123"
    assert payload["username"] == "ivan_ivanov"
    assert payload["email"] == "ivan@example.ru"
    assert "exp" in payload
    assert "iat" in payload


def test_access_token_tampering_rejected():
    data = {"sub": "user_legit"}
    token = auth.create_access_token(data=data)
    parts = token.split(".")

    # Tamper with payload (modify middle segment)
    tampered_token = f"{parts[0]}.eyJuZXdfZGF0YSI6IDF9.{parts[2]}"
    assert auth.decode_access_token(tampered_token) is None

    # Tamper with signature
    tampered_sig_token = f"{parts[0]}.{parts[1]}.invalid_signature"
    assert auth.decode_access_token(tampered_sig_token) is None

    # Malformed token
    assert auth.decode_access_token("not-a-jwt") is None
    assert auth.decode_access_token("") is None


def test_access_token_expiration():
    data = {"sub": "user_expired"}
    # Token expired 5 minutes ago
    token = auth.create_access_token(data=data, expires_delta=timedelta(seconds=-300))
    payload = auth.decode_access_token(token)
    assert payload is None


# =============================================================================
# Database User Model & CRUD Tests
# =============================================================================

def test_create_and_retrieve_user(db):
    user = crud.create_user(
        db,
        username="testuser",
        email="test@utilitylens.ru",
        password="secretpassword",
        user_id="user_custom_001",
    )

    assert user.id is not None
    assert user.user_id == "user_custom_001"
    assert user.username == "testuser"
    assert user.email == "test@utilitylens.ru"
    assert auth.verify_password("secretpassword", user.hashed_password) is True

    # Retrieve by user_id
    by_user_id = crud.get_user_by_user_id(db, "user_custom_001")
    assert by_user_id is not None
    assert by_user_id.username == "testuser"

    # Retrieve by username
    by_username = crud.get_user_by_username(db, "testuser")
    assert by_username is not None
    assert by_username.id == user.id

    # Retrieve by email (case insensitive)
    by_email_lower = crud.get_user_by_email(db, "test@utilitylens.ru")
    assert by_email_lower is not None
    by_email_upper = crud.get_user_by_email(db, "TEST@UTILITYLENS.RU")
    assert by_email_upper is not None
    assert by_email_upper.id == user.id

    # Non-existent
    assert crud.get_user_by_username(db, "nonexistent") is None
    assert crud.get_user_by_email(db, "nonexistent@example.com") is None


def test_user_bill_and_comparison_relationships(db):
    user = crud.create_user(
        db,
        username="owner",
        email="owner@utilitylens.ru",
        password="password123",
        user_id="user_owner_01",
    )

    # Create Bill linked to user
    bill = models.Bill(
        bill_id="bill_test_link_01",
        user_id=user.user_id,
        period="2026-10",
        address="г. Владивосток, ул. Светланская, д. 10",
        total_amount=Decimal("4500.00"),
    )
    db.add(bill)

    # Create Comparison linked to user
    comparison = models.Comparison(
        comparison_id="cmp_test_link_01",
        user_id=user.user_id,
        prev_bill_id=bill.bill_id,
        curr_bill_id=bill.bill_id,
        delta_abs=Decimal("500.00"),
        delta_pct=Decimal("11.11"),
        status_level="yellow",
        factor_breakdown={},
        summary_data={},
    )
    db.add(comparison)
    db.commit()

    # Refresh user to verify back_populates
    db.refresh(user)
    assert len(user.bills) == 1
    assert user.bills[0].bill_id == "bill_test_link_01"
    assert user.bills[0].user.user_id == user.user_id

    assert len(user.comparisons) == 1
    assert user.comparisons[0].comparison_id == "cmp_test_link_01"
    assert user.comparisons[0].user.user_id == user.user_id

    # Test helper functions
    user_bills = crud.get_user_bills(db, user.user_id)
    assert len(user_bills) == 1
    assert user_bills[0].bill_id == "bill_test_link_01"

    user_cmps = crud.get_user_comparisons(db, user.user_id)
    assert len(user_cmps) == 1
    assert user_cmps[0].comparison_id == "cmp_test_link_01"


def test_demo_user_seed(db):
    # Seed demo user
    demo = crud.get_user_by_email(db, "demo@utilitylens.ru")
    assert demo is None

    # Simulate init_db seeding
    created_demo = crud.create_user(
        db,
        username="demo",
        email="demo@utilitylens.ru",
        password="demo123",
        user_id="user_demo_01",
    )
    assert created_demo.user_id == "user_demo_01"
    assert created_demo.username == "demo"
    assert auth.verify_password("demo123", created_demo.hashed_password) is True


def test_get_current_user_dependency(db):
    user = crud.create_user(
        db,
        username="auth_user",
        email="auth_user@example.com",
        password="pass",
        user_id="user_auth_99",
    )

    token = auth.create_access_token(
        data={"sub": user.user_id, "username": user.username, "email": user.email}
    )

    # Valid token
    current = auth.get_current_user(token=token, db=db)
    assert current.user_id == user.user_id

    # Bearer prefix stripped correctly
    current_bearer = auth.get_current_user(token=f"Bearer {token}", db=db)
    assert current_bearer.user_id == user.user_id

    # Invalid token raises exception
    with pytest.raises(Exception):
        auth.get_current_user(token="invalid_token", db=db)

    # Missing token raises exception
    with pytest.raises(Exception):
        auth.get_current_user(token="", db=db)

    # Optional user fallback
    optional_user = auth.get_current_user_optional(token=token, db=db)
    assert optional_user.user_id == user.user_id

    # Optional without token falls back to demo user or None
    no_token_user = auth.get_current_user_optional(token=None, db=db)
    # Since demo user isn't created in this test, returns None
    assert no_token_user is None
