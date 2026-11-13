"""Routes for listing the available demo cases."""

import json
from typing import List

from fastapi import APIRouter

from app import CASES_DIR

router = APIRouter()


def _list_cases() -> List[dict]:
    cases: List[dict] = []
    if not CASES_DIR.exists():
        return cases
    for case_dir in sorted(CASES_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        meta_path = case_dir / "meta.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta.setdefault("case_id", case_dir.name)
        cases.append(meta)
    return cases


@router.get("/cases")
def list_cases() -> dict:
    return {"cases": _list_cases()}
