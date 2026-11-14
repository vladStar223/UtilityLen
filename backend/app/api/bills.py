"""API routes for uploading bills, querying user bills history and comparisons history."""

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
except ImportError:
    # Graceful fallback for offline static analysis or minimal host test environments
    class APIRouter:  # type: ignore
        def __init__(self, *args, **kwargs):
            self.routes = []

        def get(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

        def post(self, *args, **kwargs):
            def decorator(f):
                return f
            return decorator

    def Depends(dependency=None):  # type: ignore
        return dependency

    def File(*args, **kwargs):  # type: ignore
        return None

    class HTTPException(Exception):  # type: ignore
        def __init__(self, status_code: int, detail: Any = None, headers: Optional[dict] = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class UploadFile:  # type: ignore
        def __init__(self, filename: str = "", file: Any = None, content_type: str = ""):
            self.filename = filename
            self.file = file
            self.content_type = content_type

        async def read(self) -> bytes:
            if hasattr(self.file, "read"):
                res = self.file.read()
                return res if isinstance(res, bytes) else res.encode("utf-8")
            return b""

    class _Status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401
        HTTP_404_NOT_FOUND = 404
        HTTP_500_INTERNAL_SERVER_ERROR = 500

    status = _Status()  # type: ignore
from sqlalchemy.orm import Session

from app.agent.parser import DocumentParser
from app.core.analyzer import analyze
from app.core.auth import get_current_user_optional
from app.core.logging import logger
from app.core.models import (
    AnomalyItem,
    ComparisonReport,
    FactorBreakdown,
    SummaryReport,
)
from app.db import crud
from app.db.database import get_db
from app.db.models import User
from app.services.comparison_service import ComparisonService, _run_normative_audit

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

bills_router = APIRouter()
comparisons_router = APIRouter()


def _resolve_user(db: Session, user: Optional[User]) -> User:
    """Ensure an active user context, falling back to demo user if unauthenticated."""
    if user is not None:
        return user
    demo = crud.get_user_by_email(db, "demo@utilitylens.ru")
    if demo is None:
        demo = crud.create_user(
            db,
            username="demo",
            email="demo@utilitylens.ru",
            password="demo123",
            user_id="user_demo_01",
            first_name="Иван",
            last_name="Иванов",
            phone="+7 (900) 123-45-67",
            personal_account="40702810100000001234",
            address="г. Владивосток, ул. Светланская, д. 45, кв. 12",
        )
    return demo



def _get_comparison_report(db: Session, comparison_id: str) -> Optional[ComparisonReport]:
    """Retrieve comparison report from in-memory / redis cache or database."""
    # 1. Check cache first
    try:
        from app.agent.tools import get_report

        cached = get_report(comparison_id)
        if cached and "report" in cached:
            return cached["report"]
    except Exception:
        pass

    # 2. Check DB
    cmp = crud.get_comparison(db, comparison_id)
    if cmp is None:
        return None

    # Reconstruct from linked bills if available
    if cmp.curr_bill_id:
        curr_b = crud.get_bill(db, cmp.curr_bill_id)
        if curr_b:
            curr_doc = crud.bill_to_document(curr_b)
            if cmp.prev_bill_id:
                prev_b = crud.get_bill(db, cmp.prev_bill_id)
                if prev_b:
                    prev_doc = crud.bill_to_document(prev_b)
                    report = analyze(prev_doc, curr_doc)
                    report.comparison_id = cmp.comparison_id
                    return report
            report = _run_normative_audit(curr_doc)
            report.comparison_id = cmp.comparison_id
            return report

    # Fallback from stored comparison data
    anomalies = [
        AnomalyItem(
            code=a.code,
            severity=a.severity,
            service_category=a.service_category,
            title=a.title,
            impact_rub=float(a.impact_rub),
            hint=a.hint,
        )
        for a in cmp.anomalies
    ]
    stored_items: List[ServiceItem] = []
    summary_dict = dict(cmp.summary_data or {})
    if "items" in summary_dict:
        raw_items = summary_dict.pop("items")
        if isinstance(raw_items, list):
            stored_items = [ServiceItem(**it) for it in raw_items if isinstance(it, dict)]

    return ComparisonReport(
        comparison_id=cmp.comparison_id,
        summary=SummaryReport(**summary_dict),
        factor_breakdown=FactorBreakdown(**cmp.factor_breakdown),
        anomalies=anomalies,
        items=stored_items,
    )


# ---------------------------------------------------------------------------
# Bills endpoints
# ---------------------------------------------------------------------------


@bills_router.post(
    "/upload",
    response_model=ComparisonReport,
    summary="Загрузка квитанции ЖКХ",
    description="Принимает файл квитанции (PDF, PNG, JPG, JSON), производит распознавание и факторный анализ.",
)
async def upload_bill(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> ComparisonReport:
    active_user = _resolve_user(db, user)

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Загруженный файл пуст.",
        )
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Размер файла превышает лимит {MAX_FILE_SIZE_BYTES // (1024 * 1024)} МБ.",
        )

    try:
        bill_doc = await DocumentParser.parse_file(
            content=content,
            filename=file.filename or "bill",
            mime_type=file.content_type or "",
        )
    except Exception as exc:
        logger.warning("Failed to parse bill file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Не удалось обработать квитанцию: {exc}",
        )

    try:
        report = ComparisonService.process_uploaded_bill(
            db=db,
            curr_bill=bill_doc,
            user_id=active_user.user_id,
        )
        return report
    except Exception as exc:
        logger.exception("Error processing uploaded bill: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка факторного анализа квитанции: {exc}",
        )


@bills_router.get(
    "/history",
    summary="История загруженных квитанций",
    description="Возвращает список всех квитанций текущего пользователя.",
)
def get_bills_history(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> List[Dict[str, Any]]:
    active_user = _resolve_user(db, user)
    bills = crud.get_user_bills(db, active_user.user_id)
    return [
        {
            "bill_id": b.bill_id,
            "period": b.period,
            "address": b.address,
            "total_amount": float(b.total_amount),
            "created_at": b.created_at.isoformat() if b.created_at else "",
        }
        for b in bills
    ]


# ---------------------------------------------------------------------------
# Comparisons endpoints
# ---------------------------------------------------------------------------


@comparisons_router.get(
    "/history",
    summary="История сравнений пользователя",
    description="Возвращает список всех проведённых сравнений и расчётов текущего пользователя.",
)
def get_comparisons_history(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_current_user_optional),
) -> List[Dict[str, Any]]:
    active_user = _resolve_user(db, user)
    comparisons = crud.get_user_comparisons(db, active_user.user_id)
    return [
        {
            "comparison_id": c.comparison_id,
            "delta_abs": float(c.delta_abs),
            "delta_pct": float(c.delta_pct),
            "status_level": c.status_level,
            "created_at": c.created_at.isoformat() if c.created_at else "",
            "summary": c.summary_data,
        }
        for c in comparisons
    ]


@comparisons_router.get(
    "/{comparison_id}",
    response_model=ComparisonReport,
    summary="Получение сохранённого отчёта сравнения",
    description="Возвращает отчёт факторного анализа по его ID из кэша или БД.",
)
def get_comparison(
    comparison_id: str,
    db: Session = Depends(get_db),
) -> ComparisonReport:
    report = _get_comparison_report(db, comparison_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Отчёт сравнения '{comparison_id}' не найден.",
        )
    return report
