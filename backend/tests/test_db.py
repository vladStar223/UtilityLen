"""Tests for the SQLAlchemy models and CRUD helpers against SQLite."""

import re
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.analyzer import analyze
from app.core.models import BillDocument
from app.db import crud, models  # noqa: F401  (register models on Base.metadata)
from app.db.database import Base

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


def test_save_and_get_bill(db):
    prev, _ = _load_case()

    crud.save_bill(db, prev)
    saved = crud.get_bill(db, prev.bill_id)

    assert saved is not None
    assert saved.bill_id == "bill_2026_10_001"
    assert saved.period == "2026-10"
    assert saved.total_amount == Decimal("5420.00")
    assert saved.qr_verified is True
    assert len(saved.services) == 3
    assert len(saved.meters) == 1

    assert {s.service_code for s in saved.services} == {
        "cold_water",
        "heating",
        "maintenance",
    }
    meter = saved.meters[0]
    assert meter.meter_id == "CW-9921"
    assert meter.current_reading == Decimal("130.000")


def test_save_bill_is_idempotent(db):
    prev, _ = _load_case()

    first = crud.save_bill(db, prev)
    second = crud.save_bill(db, prev)

    assert first.id == second.id
    assert db.query(models.Bill).count() == 1


def test_mask_qr_personal_data():
    raw = (
        "ST00012|Name=ООО УК Уютный Дом|PersonalAcc=40702810100000001234"
        "|BankName=ПАО СБЕРБАНК|CorrespAcc=30101810400000000225|Sum=542000"
    )
    masked = crud.mask_qr_personal_data(raw)

    assert "PersonalAcc=4070****1234" in masked
    assert "40702810100000001234" not in masked
    # CorrespAcc is not personal data and must remain untouched.
    assert "CorrespAcc=30101810400000000225" in masked


def test_save_bill_masks_qr_personal_acc(db):
    prev, _ = _load_case()
    assert prev.qr_data is not None
    assert "PersonalAcc=40702810100000001234" in prev.qr_data

    saved = crud.save_bill(db, prev)

    assert saved.qr_data is not None
    assert "PersonalAcc=40702810100000001234" not in saved.qr_data
    assert "PersonalAcc=4070****1234" in saved.qr_data


def test_get_bill_missing_returns_none(db):
    assert crud.get_bill(db, "bill_unknown") is None


def test_save_and_get_comparison(db):
    prev, curr = _load_case()
    report = analyze(prev, curr)

    crud.save_comparison(db, report, prev, curr)
    saved = crud.get_comparison(db, report.comparison_id)

    assert saved is not None
    assert re.fullmatch(r"cmp-[0-9a-f]{32}", saved.comparison_id)
    assert float(saved.delta_abs) == 1470.50
    assert float(saved.delta_pct) == 27.13
    assert saved.status_level == "red"
    assert saved.prev_bill_id == "bill_2026_10_001"
    assert saved.curr_bill_id == "bill_2026_11_001"
    assert saved.factor_breakdown["tariff_effect_rub"] == 144.80
    assert saved.summary_data["curr_total"] == 6890.50
    assert len(saved.anomalies) == 2

    codes = {a.code for a in saved.anomalies}
    assert "APPLYING_COEFF_1_5" in codes
    assert "METER_VERIFICATION_DUE" in codes


def test_save_comparison_is_idempotent(db):
    prev, curr = _load_case()
    report = analyze(prev, curr)

    first = crud.save_comparison(db, report, prev, curr)
    second = crud.save_comparison(db, report, prev, curr)

    assert first.id == second.id
    assert db.query(models.Comparison).count() == 1
    assert db.query(models.ComparisonAnomaly).count() == 2


def test_get_comparison_missing_returns_none(db):
    assert crud.get_comparison(db, "cmp_unknown") is None


def test_chat_messages_roundtrip(db):
    crud.save_chat_message(db, "cmp_1", "user", "Почему выросла сумма?")
    crud.save_chat_message(
        db,
        "cmp_1",
        "assistant",
        "Тариф вырос на 8.3%",
        tool_calls={"name": "lookup_glossary"},
    )

    history = crud.get_chat_history(db, "cmp_1")

    assert len(history) == 2
    assert history[0].role == "user"
    assert history[0].content == "Почему выросла сумма?"
    assert history[1].role == "assistant"
    assert history[1].tool_calls == {"name": "lookup_glossary"}
