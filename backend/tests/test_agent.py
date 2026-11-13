"""Unit tests for the AI-lawyer agent tools and claim integrity."""

import asyncio
import json
from pathlib import Path

from app.agent import runner, tools
from app.core.analyzer import analyze
from app.core.models import BillDocument

REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = REPO_ROOT / "data" / "cases" / "case_02_coeff_15"


def _compute_report():
    prev = BillDocument.model_validate_json(
        (CASE_DIR / "prev_bill.json").read_text(encoding="utf-8")
    )
    curr = BillDocument.model_validate_json(
        (CASE_DIR / "curr_bill.json").read_text(encoding="utf-8")
    )
    report = analyze(prev, curr)
    tools.store_comparison(report.comparison_id, report, curr, prev)
    return report


def test_lookup_glossary_returns_entry():
    entry = tools.lookup_glossary("cold_water")
    assert entry is not None
    assert entry["name"]
    assert "354" in entry["law_ref"]


def test_get_anomaly_action_plan_returns_steps():
    plan = tools.get_anomaly_action_plan("APPLYING_COEFF_1_5")
    assert plan is not None
    assert plan["explanation"]
    assert isinstance(plan["action_steps"], list)
    assert len(plan["action_steps"]) >= 1


def test_draft_claim_mentions_exact_amount_and_law():
    report = _compute_report()
    claim = tools.draft_uk_claim(report.comparison_id, "APPLYING_COEFF_1_5")
    assert claim is not None
    assert "245.18" in claim["text"]
    assert "60(1)" in claim["text"]


def test_claim_sum_is_consistent():
    report = _compute_report()
    claim = tools.draft_uk_claim(report.comparison_id, "APPLYING_COEFF_1_5")
    # The overpayment figure in the claim must equal the report impact exactly.
    assert "245.18" in claim["text"]
    anomaly = next(
        a for a in report.anomalies if a.code == "APPLYING_COEFF_1_5"
    )
    assert anomaly.impact_rub == 245.18


def _decode_sse_tokens(frames):
    tokens = []
    types = []
    for frame in frames:
        for line in frame.split("\n"):
            if line.startswith("data: "):
                payload = json.loads(line[len("data: "):])
                types.append(payload.get("type"))
                if payload.get("type") == "token":
                    tokens.append(payload.get("content", ""))
    return "".join(tokens), types


def test_stream_mentions_exact_amount_and_law():
    report = _compute_report()

    async def collect():
        frames = []
        async for frame in runner.generate_stream(report.comparison_id, "Что с ХВС?", []):
            frames.append(frame)
        return frames

    frames = asyncio.run(collect())
    text, types = _decode_sse_tokens(frames)
    assert "token" in types
    assert "done" in types
    assert "tool_call" in types
    assert "245.18" in text
    assert "60(1)" in text


def test_mask_personal_account():
    masked = runner.mask_personal_account("40702810100000001234")
    assert masked == "40702***1234"
