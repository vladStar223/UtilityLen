"""Route for the deterministic factor-analysis report."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import CASES_DIR
from app.agent.tools import store_comparison
from app.core.analyzer import analyze
from app.core.models import BillDocument, ComparisonReport
from app.db import crud
from app.db.database import get_db

router = APIRouter()


class CompareRequest(BaseModel):
    case_id: Optional[str] = Field(
        default=None,
        description="ID демо-кейса (альтернатива загрузке квитанций)",
        examples=["vladivostok-lenina-10"],
    )
    prev_bill: Optional[BillDocument] = Field(
        default=None,
        description="Квитанция за предыдущий период",
    )
    curr_bill: Optional[BillDocument] = Field(
        default=None,
        description="Квитанция за текущий период",
    )


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


@router.post(
    "/compare",
    response_model=ComparisonReport,
    summary="Факторный анализ двух квитанций",
    description="""
Запускает детерминированный факторный анализ по двум квитанциям.

Можно указать либо `case_id` для загрузки готового демо-кейса, либо передать
две квитанции (`prev_bill` и `curr_bill`) напрямую. Результат включает:
сводку, факторный разбор (вклад тарифов, объёмов, перерасчётов, новых услуг),
список аномалий и детализацию по каждой услуге.
""",
    responses={
        200: {
            "description": "Сравнение успешно выполнено, возвращён отчёт",
            "content": {
                "application/json": {
                    "example": {
                        "comparison_id": "cmp-20240215-abc123",
                        "summary": {
                            "prev_period": "2024-01",
                            "curr_period": "2024-02",
                            "prev_total": 4200.50,
                            "curr_total": 4520.75,
                            "delta_abs": 320.25,
                            "delta_pct": 7.62,
                            "qr_verified": True,
                            "status_level": "warning",
                        },
                        "factor_breakdown": {
                            "tariff_effect_rub": 150.50,
                            "volume_effect_rub": 200.00,
                            "recalculation_effect_rub": -30.25,
                            "new_services_effect_rub": 0.0,
                        },
                        "anomalies": [],
                        "items": [],
                    }
                }
            },
        },
        400: {
            "description": "Некорректный запрос: не указан case_id и не переданы обе квитанции",
            "content": {
                "application/json": {
                    "example": {"detail": "Provide either 'case_id' or both 'prev_bill' and 'curr_bill'"}
                }
            },
        },
        404: {
            "description": "Демо-кейс с указанным case_id не найден или неполный",
            "content": {
                "application/json": {
                    "example": {"detail": "Case 'unknown-case' not found"}
                }
            },
        },
    },
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "by_case_id": {
                            "summary": "Анализ по демо-кейсу",
                            "value": {"case_id": "vladivostok-lenina-10"},
                        },
                        "by_bills": {
                            "summary": "Анализ по загруженным квитанциям",
                            "value": {
                                "prev_bill": {
                                    "bill_id": "bill-001",
                                    "period": "2024-01",
                                    "address": "г. Владивосток, ул. Ленина, 10",
                                    "total_amount": 4200.50,
                                    "services": [
                                        {
                                            "service_code": "cold_water",
                                            "raw_name": "Холодное водоснабжение",
                                            "unit": "м3",
                                            "volume": 10.5,
                                            "tariff": 42.00,
                                            "total": 441.00,
                                        }
                                    ],
                                },
                                "curr_bill": {
                                    "bill_id": "bill-002",
                                    "period": "2024-02",
                                    "address": "г. Владивосток, ул. Ленина, 10",
                                    "total_amount": 4520.75,
                                    "services": [
                                        {
                                            "service_code": "cold_water",
                                            "raw_name": "Холодное водоснабжение",
                                            "unit": "м3",
                                            "volume": 12.5,
                                            "tariff": 45.50,
                                            "total": 568.75,
                                        }
                                    ],
                                },
                            },
                        },
                    }
                }
            }
        }
    },
)
def compare(request: CompareRequest, db: Session = Depends(get_db)) -> ComparisonReport:
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

    try:
        crud.save_comparison(db, report, prev_bill, curr_bill)
    except Exception:
        db.rollback()

    return report
