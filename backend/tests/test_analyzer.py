"""Unit tests for the deterministic factor-analysis kernel.

Uses the reference demo case ``data/cases/case_02_coeff_15`` and checks that
the produced report matches the frozen contract ``contracts/compare_response.json``
in structure and, for the shared figures, in value.
"""

import json
from pathlib import Path

import pytest

from app.core.analyzer import analyze
from app.core.models import BillDocument, ComparisonReport

REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = REPO_ROOT / "data" / "cases" / "case_02_coeff_15"
CONTRACT_PATH = REPO_ROOT / "contracts" / "compare_response.json"


def _load_case():
    prev = BillDocument.model_validate_json(
        (CASE_DIR / "prev_bill.json").read_text(encoding="utf-8")
    )
    curr = BillDocument.model_validate_json(
        (CASE_DIR / "curr_bill.json").read_text(encoding="utf-8")
    )
    return prev, curr


@pytest.fixture(scope="module")
def report() -> ComparisonReport:
    prev, curr = _load_case()
    return analyze(prev, curr)


def test_structure_matches_contract(report):
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert set(report.model_dump().keys()) == set(contract.keys())
    assert set(report.summary.model_dump().keys()) == set(contract["summary"].keys())
    assert set(report.factor_breakdown.model_dump().keys()) == set(
        contract["factor_breakdown"].keys()
    )
    assert all(
        set(a.model_dump().keys()) == set(contract["anomalies"][0].keys())
        for a in report.anomalies
    )
    assert all(
        set(i.model_dump().keys()) == set(contract["items"][0].keys())
        for i in report.items
    )


def test_summary_values(report):
    s = report.summary
    assert s.prev_period == "2026-10"
    assert s.curr_period == "2026-11"
    assert s.prev_total == 5420.00
    assert s.curr_total == 6890.50
    assert s.delta_abs == 1470.50
    assert s.delta_pct == 27.13
    assert s.qr_verified is True
    assert s.status_level == "red"


def test_cold_water_item_matches_contract(report):
    item = next(i for i in report.items if i.category == "cold_water")
    assert item.display_name == "Холодное водоснабжение (ХВС)"
    assert item.unit == "м3"
    assert item.prev_volume == 6.0
    assert item.curr_volume == 8.2
    assert item.prev_tariff == 54.00
    assert item.curr_tariff == 59.80
    assert item.prev_total == 324.00
    assert item.curr_total == 735.54
    assert item.delta_abs == 411.54
    assert item.delta_pct == 127.02
    assert item.tariff_delta_rub == 34.80
    assert item.volume_delta_rub == 131.56
    assert item.coeff_surcharge_rub == 245.18
    assert item.status == "red"


def test_applying_coeff_1_5_anomaly(report):
    anomaly = next(
        a for a in report.anomalies if a.code == "APPLYING_COEFF_1_5"
    )
    assert anomaly.severity == "red"
    assert anomaly.service_category == "cold_water"
    assert anomaly.title == "Применен повышающий коэффициент 1.5"
    assert anomaly.impact_rub == 245.18


def test_line_delta_balance_converges(report):
    line_delta = round(sum(i.delta_abs for i in report.items), 2)
    assert line_delta == report.summary.delta_abs


def test_factor_breakdown_balance_converges(report):
    fb = report.factor_breakdown
    factor_sum = round(
        fb.tariff_effect_rub
        + fb.volume_effect_rub
        + fb.recalculation_effect_rub
        + fb.new_services_effect_rub,
        2,
    )
    assert factor_sum == report.summary.delta_abs


def test_factor_breakdown_exact_values(report):
    fb = report.factor_breakdown
    assert fb.tariff_effect_rub == 144.80
    assert fb.volume_effect_rub == 856.56
    assert fb.recalculation_effect_rub == 469.14
    assert fb.new_services_effect_rub == 0.00
