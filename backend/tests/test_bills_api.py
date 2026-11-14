"""Tests for bill upload, bill history, and comparisons history API endpoints."""

import io
import json
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.bills import (
    HTTPException,
    UploadFile,
    get_bills_history,
    get_comparison,
    get_comparisons_history,
    upload_bill,
)
from app.core.auth import create_access_token
from app.core.models import ComparisonReport
from app.db import crud
from app.db.database import Base
from app.db.models import User


class MockUploadFile:
    """Mock for FastAPI UploadFile during unit testing."""

    def __init__(self, filename: str, content: bytes, content_type: str = "application/json"):
        self.filename = filename
        self._content = content
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._content


@pytest.fixture()
def db():
    """In-memory SQLite session isolated per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        # Seed demo user
        crud.create_user(
            session,
            username="demo",
            email="demo@utilitylens.ru",
            password="demo123",
            user_id="user_demo_01",
        )
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_bill_data():
    return {
        "bill_id": "test_bill_upload_oct_2026",
        "period": "2026-10",
        "address": "г. Владивосток, Океанский пр-кт, 10",
        "payer": "Петров П.П.",
        "total_amount": 2500.0,
        "services": [
            {
                "service_code": "cold_water",
                "raw_name": "Холодное водоснабжение",
                "unit": "м3",
                "volume": 5.0,
                "tariff": 50.0,
                "coefficient": 1.0,
                "recalculation": 0.0,
                "penalty": 0.0,
                "total": 250.0,
            }
        ],
    }


@pytest.fixture
def sample_bill_nov_data():
    return {
        "bill_id": "test_bill_upload_nov_2026",
        "period": "2026-11",
        "address": "г. Владивосток, Океанский пр-кт, 10",
        "payer": "Петров П.П.",
        "total_amount": 3100.0,
        "services": [
            {
                "service_code": "cold_water",
                "raw_name": "Холодное водоснабжение",
                "unit": "м3",
                "volume": 6.0,
                "tariff": 50.0,
                "coefficient": 1.0,
                "recalculation": 0.0,
                "penalty": 0.0,
                "total": 300.0,
            }
        ],
    }


@pytest.mark.anyio
async def test_upload_bill_json_success(db, sample_bill_data):
    """Test uploading a valid JSON bill triggers parsing and returns a ComparisonReport."""
    file_bytes = json.dumps(sample_bill_data).encode("utf-8")
    upload = MockUploadFile("october_bill.json", file_bytes, "application/json")

    report = await upload_bill(file=upload, db=db, user=None)

    assert isinstance(report, ComparisonReport)
    assert report.comparison_id.startswith("cmp-")
    assert report.summary.curr_period == "2026-10"
    assert report.summary.curr_total == 2500.0
    assert report.factor_breakdown is not None
    assert len(report.items) == 1
    assert report.items[0].curr_total == 250.0


@pytest.mark.anyio
async def test_upload_bill_empty_file(db):
    """Test uploading an empty file raises 400 Bad Request."""
    upload = MockUploadFile("empty.json", b"", "application/json")
    with pytest.raises(HTTPException) as exc_info:
        await upload_bill(file=upload, db=db, user=None)
    assert exc_info.value.status_code == 400
    assert "пуст" in str(exc_info.value.detail).lower()


@pytest.mark.anyio
async def test_upload_bill_oversized_file(db):
    """Test uploading a file > 10MB raises 400 Bad Request."""
    oversized = b"a" * (10 * 1024 * 1024 + 1)
    upload = MockUploadFile("huge.json", oversized, "application/json")
    with pytest.raises(HTTPException) as exc_info:
        await upload_bill(file=upload, db=db, user=None)
    assert exc_info.value.status_code == 400
    assert "лимит" in str(exc_info.value.detail).lower()


@pytest.mark.anyio
async def test_upload_bill_invalid_json(db):
    """Test uploading malformed content raises 400 Bad Request."""
    upload = MockUploadFile("broken.json", b"not a valid json {{{{", "application/json")
    with pytest.raises(HTTPException) as exc_info:
        await upload_bill(file=upload, db=db, user=None)
    assert exc_info.value.status_code == 400
    assert "не удалось" in str(exc_info.value.detail).lower()


@pytest.mark.anyio
async def test_upload_bill_non_utility_json_rejected(db):
    """Test uploading arbitrary non-utility JSON raises 400 with helpful error."""
    arbitrary = json.dumps({"arbitrary_field": "some_value"}).encode("utf-8")
    upload = MockUploadFile("not_a_bill.json", arbitrary, "application/json")
    with pytest.raises(HTTPException) as exc_info:
        await upload_bill(file=upload, db=db, user=None)
    assert exc_info.value.status_code == 400
    assert "не является квитанцией жкх" in str(exc_info.value.detail).lower()


@pytest.mark.anyio
async def test_get_bills_history(db, sample_bill_data):
    """Test GET /api/v1/bills/history returns the list of uploaded bills."""
    file_bytes = json.dumps(sample_bill_data).encode("utf-8")
    upload = MockUploadFile("october_bill.json", file_bytes, "application/json")
    await upload_bill(file=upload, db=db, user=None)

    bills = get_bills_history(db=db, user=None)
    assert isinstance(bills, list)
    assert len(bills) >= 1

    matching = [b for b in bills if b["bill_id"] == sample_bill_data["bill_id"]]
    assert len(matching) == 1
    assert matching[0]["address"] == sample_bill_data["address"]
    assert matching[0]["total_amount"] == sample_bill_data["total_amount"]
    assert matching[0]["period"] == "2026-10"


@pytest.mark.anyio
async def test_get_comparisons_history(db, sample_bill_data):
    """Test GET /api/v1/comparisons/history returns user's comparisons."""
    file_bytes = json.dumps(sample_bill_data).encode("utf-8")
    upload = MockUploadFile("october_bill.json", file_bytes, "application/json")
    report = await upload_bill(file=upload, db=db, user=None)

    comparisons = get_comparisons_history(db=db, user=None)
    assert isinstance(comparisons, list)
    assert len(comparisons) >= 1

    matching = [c for c in comparisons if c["comparison_id"] == report.comparison_id]
    assert len(matching) == 1
    assert matching[0]["delta_abs"] == 2500.0
    assert "summary" in matching[0]


@pytest.mark.anyio
async def test_get_comparison_by_id(db, sample_bill_data):
    """Test GET /api/v1/comparisons/{comparison_id} retrieves stored report."""
    file_bytes = json.dumps(sample_bill_data).encode("utf-8")
    upload = MockUploadFile("october_bill.json", file_bytes, "application/json")
    created = await upload_bill(file=upload, db=db, user=None)

    fetched = get_comparison(comparison_id=created.comparison_id, db=db)
    assert fetched.comparison_id == created.comparison_id
    assert fetched.summary.curr_total == sample_bill_data["total_amount"]
    assert fetched.summary.curr_period == "2026-10"


def test_get_comparison_not_found(db):
    """Test GET /api/v1/comparisons/{unknown_id} raises 404."""
    with pytest.raises(HTTPException) as exc_info:
        get_comparison(comparison_id="cmp-non-existent-99999", db=db)
    assert exc_info.value.status_code == 404
    assert "не найден" in str(exc_info.value.detail).lower()


@pytest.mark.anyio
async def test_upload_two_consecutive_bills_factors(db, sample_bill_data, sample_bill_nov_data):
    """Test sequential uploading of two consecutive bills automatically runs factor comparison."""
    # 1. Upload October bill
    f_oct = json.dumps(sample_bill_data).encode("utf-8")
    rep1 = await upload_bill(
        file=MockUploadFile("oct.json", f_oct, "application/json"),
        db=db,
        user=None,
    )
    assert rep1.summary.curr_period == "2026-10"

    # 2. Upload November bill for the exact same address
    f_nov = json.dumps(sample_bill_nov_data).encode("utf-8")
    rep2 = await upload_bill(
        file=MockUploadFile("nov.json", f_nov, "application/json"),
        db=db,
        user=None,
    )

    # The November bill should factor-compare against October!
    assert rep2.summary.prev_period == "2026-10"
    assert rep2.summary.curr_period == "2026-11"
    assert rep2.summary.prev_total == 2500.0
    assert rep2.summary.curr_total == 3100.0
    assert rep2.summary.delta_abs == 600.0


@pytest.mark.anyio
async def test_upload_with_authenticated_jwt_user(db):
    """Test uploading with an explicit User object associates the bill with that user."""
    custom_user = crud.create_user(
        db,
        username="custom_user",
        email="custom_user@test.ru",
        password="secret_password",
        user_id="user_custom_test_99",
    )

    custom_bill = {
        "bill_id": "bill_jwt_custom_1",
        "period": "2026-09",
        "address": "г. Владивосток, ул. Алеутская, 20",
        "total_amount": 1800.0,
        "services": [
            {
                "service_code": "cold_water",
                "raw_name": "ХВС",
                "unit": "м3",
                "volume": 3.0,
                "tariff": 50.0,
                "total": 150.0,
            }
        ],
    }

    upload = MockUploadFile(
        "custom.json",
        json.dumps(custom_bill).encode("utf-8"),
        "application/json",
    )
    report = await upload_bill(file=upload, db=db, user=custom_user)
    assert report.summary.curr_period == "2026-09"

    user_bills = get_bills_history(db=db, user=custom_user)
    assert len(user_bills) == 1
    assert user_bills[0]["bill_id"] == "bill_jwt_custom_1"

    # Demo user should not see this bill
    demo_bills = get_bills_history(db=db, user=None)
    assert not any(b["bill_id"] == "bill_jwt_custom_1" for b in demo_bills)
