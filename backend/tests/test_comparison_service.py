"""Unit tests for the Auto-Comparison Service and User History operations."""

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.models import BillDocument, MeterReading, ServiceLine
from app.db import crud, models  # noqa: F401
from app.db.database import Base
from app.services.comparison_service import (
    ComparisonService,
    get_user_history,
    process_uploaded_bill,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = REPO_ROOT / "data" / "cases" / "case_02_coeff_15"


@pytest.fixture()
def db():
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


def _load_case():
    prev = BillDocument.model_validate_json(
        (CASE_DIR / "prev_bill.json").read_text(encoding="utf-8")
    )
    curr = BillDocument.model_validate_json(
        (CASE_DIR / "curr_bill.json").read_text(encoding="utf-8")
    )
    return prev, curr


def _make_bill(bill_id: str, user_id: str, address: str, period: str, total: float = 1000.0) -> BillDocument:
    return BillDocument(
        bill_id=bill_id,
        period=period,
        address=address,
        total_amount=total,
        services=[
            ServiceLine(
                service_code="cold_water",
                raw_name="Холодная вода",
                unit="м3",
                volume=10.0,
                tariff=50.0,
                coefficient=1.0,
                total=500.0,
            ),
            ServiceLine(
                service_code="electricity",
                raw_name="Электроэнергия",
                unit="кВт·ч",
                volume=100.0,
                tariff=5.0,
                coefficient=1.0,
                total=500.0,
            ),
        ],
        meters=[
            MeterReading(
                meter_id="MTR-1",
                service_code="cold_water",
                current_reading=100.0,
                verification_due_date="2030-01-01",
            )
        ],
    )


def test_find_previous_bill_logic(db):
    user_a = "user_alpha"
    user_b = "user_beta"

    b1 = _make_bill("b1", user_a, "ул. Светланская, 10", "2024-01")
    b2 = _make_bill("b2", user_a, "ул. Алеутская, 20", "2024-02")
    b3 = _make_bill("b3", user_b, "ул. Светланская, 10", "2024-02")

    crud.save_bill(db, b1, user_id=user_a)
    crud.save_bill(db, b2, user_id=user_a)
    crud.save_bill(db, b3, user_id=user_b)

    # 1. Exact address match for user_a
    match_exact = crud.find_previous_bill(
        db,
        user_id=user_a,
        address="ул. Светланская, 10",
        current_period="2024-03",
    )
    assert match_exact is not None
    assert match_exact.bill_id == "b1"

    # 2. Fallback to any prior bill for user_a when address has no prior record
    fallback = crud.find_previous_bill(
        db,
        user_id=user_a,
        address="ул. Океанский пр-т, 5",
        current_period="2024-03",
    )
    assert fallback is not None
    assert fallback.bill_id == "b2"  # Newest prior period (2024-02)

    # 3. None when current_period is older or equal to oldest bill
    none_match = crud.find_previous_bill(
        db,
        user_id=user_a,
        address="ул. Светланская, 10",
        current_period="2024-01",
    )
    assert none_match is None

    # 4. User isolation: user_b only sees user_b's bills
    user_b_match = crud.find_previous_bill(
        db,
        user_id=user_b,
        address="ул. Светланская, 10",
        current_period="2024-03",
    )
    assert user_b_match is not None
    assert user_b_match.bill_id == "b3"


def test_bill_to_document_roundtrip(db):
    _, curr = _load_case()
    crud.save_bill(db, curr, user_id="user_rt")

    orm_bill = crud.get_bill(db, curr.bill_id)
    assert orm_bill is not None

    doc = crud.bill_to_document(orm_bill)
    assert doc.bill_id == curr.bill_id
    assert doc.period == curr.period
    assert doc.address == curr.address
    assert doc.total_amount == curr.total_amount
    assert len(doc.services) == len(curr.services)
    assert len(doc.meters) == len(curr.meters)

    # Check service fields preserved
    cw_svc = next(s for s in doc.services if s.service_code == "cold_water")
    assert cw_svc.coefficient == 1.5
    assert cw_svc.tariff == 59.80
    assert cw_svc.volume == 8.2
    assert cw_svc.total == 735.54

    # Check meter fields preserved
    meter = doc.meters[0]
    assert meter.meter_id == "CW-9921"
    assert meter.verification_due_date == "2026-10-15"


def test_process_uploaded_bill_first_bill_normative_audit(db):
    _, curr = _load_case()
    user_id = "user_audit_1"

    report = process_uploaded_bill(db, curr, user_id=user_id)

    assert report.comparison_id.startswith("cmp-")
    assert report.summary.prev_period == ""
    assert report.summary.curr_period == curr.period
    assert report.summary.prev_total == 0.0
    assert report.summary.curr_total == curr.total_amount
    assert report.summary.delta_abs == curr.total_amount
    assert report.summary.delta_pct == 0.0
    assert report.summary.status_level == "warning"

    # Factor breakdown should be 0.0 for first bill
    assert report.factor_breakdown.tariff_effect_rub == 0.0
    assert report.factor_breakdown.volume_effect_rub == 0.0
    assert report.factor_breakdown.recalculation_effect_rub == 0.0
    assert report.factor_breakdown.new_services_effect_rub == 0.0

    # Anomalies should detect:
    # 1) APPLYING_COEFF_1_5 with impact 735.54 - 59.80 * 8.2 = 245.18
    coeff_anomaly = next((a for a in report.anomalies if a.code == "APPLYING_COEFF_1_5"), None)
    assert coeff_anomaly is not None
    assert coeff_anomaly.severity == "red"
    assert coeff_anomaly.impact_rub == 245.18

    # 2) METER_VERIFICATION_DUE because 2026-10-15 is expired relative to 2026-11
    meter_anomaly = next((a for a in report.anomalies if a.code == "METER_VERIFICATION_DUE"), None)
    assert meter_anomaly is not None
    assert meter_anomaly.severity == "yellow"

    # Services items check
    assert len(report.items) == len(curr.services)

    # Persisted in DB
    saved = crud.get_comparison(db, report.comparison_id)
    assert saved is not None
    assert saved.user_id == user_id
    assert saved.prev_bill_id is None
    assert saved.curr_bill_id == curr.bill_id


def test_process_uploaded_bill_with_prior_bill_factor_analysis(db):
    prev, curr = _load_case()
    user_id = "user_flow_1"

    # 1. Process previous bill first
    report_prev = process_uploaded_bill(db, prev, user_id=user_id)
    assert report_prev.summary.prev_period == ""

    # 2. Process current bill
    report_curr = ComparisonService.process_uploaded_bill(db, curr, user_id=user_id)

    assert report_curr.summary.prev_period == prev.period
    assert report_curr.summary.curr_period == curr.period
    assert report_curr.summary.prev_total == prev.total_amount
    assert report_curr.summary.curr_total == curr.total_amount
    expected_delta = round(curr.total_amount - prev.total_amount, 2)
    assert report_curr.summary.delta_abs == expected_delta

    # Factor breakdown should have non-zero effects computed by analyze()
    total_effects = (
        report_curr.factor_breakdown.tariff_effect_rub
        + report_curr.factor_breakdown.volume_effect_rub
        + report_curr.factor_breakdown.recalculation_effect_rub
        + report_curr.factor_breakdown.new_services_effect_rub
    )
    assert round(total_effects, 2) == expected_delta

    # DB persistence check
    saved = crud.get_comparison(db, report_curr.comparison_id)
    assert saved is not None
    assert saved.user_id == user_id
    assert saved.prev_bill_id == prev.bill_id
    assert saved.curr_bill_id == curr.bill_id


def test_get_user_history(db):
    prev, curr = _load_case()
    user_id = "user_hist_1"

    process_uploaded_bill(db, prev, user_id=user_id)
    process_uploaded_bill(db, curr, user_id=user_id)

    history = get_user_history(db, user_id)

    # Dict access
    assert "bills" in history
    assert "comparisons" in history
    assert len(history["bills"]) == 2
    assert len(history["comparisons"]) == 2

    # Attribute access
    assert len(history.bills) == 2
    assert len(history.comparisons) == 2

    # Check ordering by period descending: curr (2026-11) before prev (2026-10)
    assert history.bills[0].period == "2026-11"
    assert history.bills[1].period == "2026-10"

    # Service wrapper test
    history_via_service = ComparisonService.get_user_history(db, user_id)
    assert len(history_via_service.bills) == 2


def test_process_uploaded_bill_normative_audit_no_anomalies(db):
    user_id = "user_clean_1"
    clean_bill = _make_bill("clean_001", user_id, "ул. Ленина, 1", "2025-05", total=1000.0)

    report = process_uploaded_bill(db, clean_bill, user_id=user_id)

    assert report.summary.status_level == "ok"
    assert len(report.anomalies) == 0
    assert report.summary.prev_period == ""
    assert report.summary.curr_period == "2025-05"
