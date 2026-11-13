"""Route for the deterministic factor-analysis report."""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import CASES_DIR
from app.agent.tools import store_comparison
from app.core.analyzer import analyze
from app.core.models import BillDocument, ComparisonReport

router = APIRouter()


class CompareRequest(BaseModel):
    case_id: Optional[str] = None
    prev_bill: Optional[BillDocument] = None
    curr_bill: Optional[BillDocument] = None


def _load_case_bills(case_id: str):
    case_dir = CASES_DIR / case_id
    if not case_dir.is_dir():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found")

    prev_path = case_dir / "prev_bill.json"
    curr_path = case_dir / "curr_bill.json"
    if not prev_path.exists() or not curr_path.exists():
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' is incomplete")

    prev_bill = BillDocument.model_validate_json(prev_path.read_text(encoding="utf-8"))
    curr_bill = BillDocument.model_validate_json(curr_path.read_text(encoding="utf-8"))
    return prev_bill, curr_bill


@router.post("/compare", response_model=ComparisonReport)
def compare(request: CompareRequest) -> ComparisonReport:
    if request.case_id:
        prev_bill, curr_bill = _load_case_bills(request.case_id)
    elif request.prev_bill is not None and request.curr_bill is not None:
        prev_bill, curr_bill = request.prev_bill, request.curr_bill
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'case_id' or both 'prev_bill' and 'curr_bill'",
        )

    report = analyze(prev_bill, curr_bill)
    store_comparison(report.comparison_id, report, curr_bill, prev_bill)
    return report
