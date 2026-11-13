"""Routes for listing the available demo cases."""

import json
from typing import List

from fastapi import APIRouter, Depends

from app import CASES_DIR
from app.core.security import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])


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


@router.get(
    "/cases",
    summary="Список демо-кейсов Владивостока",
    description="Возвращает список доступных демо-кейсов с метаинформацией (адрес, периоды, краткое описание). Каждый кейс содержит пару квитанций для сравнения.",
    responses={
        200: {
            "description": "Список кейсов успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "cases": [
                            {
                                "case_id": "vladivostok-lenina-10",
                                "address": "г. Владивосток, ул. Ленина, д. 10, кв. 25",
                                "prev_period": "2024-01",
                                "curr_period": "2024-02",
                                "description": "Типичная квартира: рост тарифов на отопление и воду"
                            }
                        ]
                    }
                }
            },
        }
    },
)
def list_cases() -> dict:
    return {"cases": _list_cases()}
