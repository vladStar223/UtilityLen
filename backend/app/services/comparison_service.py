"""Auto-comparison service with user history lookup and normative audit.

Orchestrates saving newly uploaded utility bills, finding previous receipts
in the user's history, running factor analysis or fallback normative audits,
and persisting the resulting comparison reports.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.agent.tools import store_comparison
from app.core.analyzer import (
    _line_code,
    _verification_due,
    analyze,
)
from app.core.logging import logger
from app.core.models import (
    AnomalyItem,
    BillDocument,
    ComparisonReport,
    FactorBreakdown,
    ServiceItem,
    SummaryReport,
)
from app.core.normalizer import display_name
from app.db import crud
from app.db.models import Bill, Comparison
from app.ingestion.qr_parser import extract_sum_rub, verify_qr_sum


class UserHistory(dict):
    """Container for user receipts and comparisons supporting both dict and attribute access."""

    def __init__(self, bills: List[Bill], comparisons: List[Comparison]) -> None:
        super().__init__(bills=bills, comparisons=comparisons)

    @property
    def bills(self) -> List[Bill]:
        return self["bills"]

    @property
    def comparisons(self) -> List[Comparison]:
        return self["comparisons"]


def _run_normative_audit(curr_bill: BillDocument) -> ComparisonReport:
    """Run a single-bill normative audit when no prior receipt exists in history.

    Detects:
    * Raising coefficients (1.5 / 3.0) applied to service lines.
    * Expired meter verification due dates.
    """
    anomalies: List[AnomalyItem] = []

    # 1. Check services for raising coefficients
    for line in curr_bill.services:
        coeff = line.coefficient if line.coefficient is not None else 1.0
        if coeff > 1.0:
            surcharge = round(float(line.total) - float(line.tariff) * float(line.volume), 2)
            code = _line_code(line)
            if coeff < 3.0:
                anomalies.append(
                    AnomalyItem(
                        code="APPLYING_COEFF_1_5",
                        severity="red",
                        service_category=code,
                        title="Применен повышающий коэффициент 1.5",
                        impact_rub=surcharge,
                        hint=(
                            "Истек срок поверки счетчика ХВС или не передавались "
                            "показания более 3 месяцев."
                        ),
                    )
                )
            else:
                anomalies.append(
                    AnomalyItem(
                        code="APPLYING_COEFF_3_0",
                        severity="red",
                        service_category=code,
                        title="Применен повышающий коэффициент 3.0",
                        impact_rub=surcharge,
                        hint=(
                            "Расчет переведен на норматив с повышающим коэффициентом "
                            "3.0: истек срок поверки счетчика или показания не "
                            "передавались более 3 месяцев."
                        ),
                    )
                )

    # 2. Check meters for expired verification dates
    for meter in curr_bill.meters or []:
        if not meter.verification_due_date:
            continue
        if _verification_due(meter.verification_due_date, curr_bill.period):
            anomalies.append(
                AnomalyItem(
                    code="METER_VERIFICATION_DUE",
                    severity="yellow",
                    service_category=meter.service_code,
                    title="Истек срок поверки счетчика",
                    impact_rub=0.0,
                    hint=(
                        f"Срок поверки прибора учета {meter.meter_id} истек "
                        f"{meter.verification_due_date}. Закажите поверку и "
                        "внесите данные во ФГИС «АРШИН»."
                    ),
                )
            )

    # 3. Build ServiceItem list
    items: List[ServiceItem] = []
    for line in curr_bill.services:
        code = _line_code(line)
        coeff = line.coefficient if line.coefficient is not None else 1.0
        has_coeff = coeff > 1.0
        coeff_surcharge = round(float(line.total) - float(line.tariff) * float(line.volume), 2) if has_coeff else 0.0

        items.append(
            ServiceItem(
                category=code,
                display_name=display_name(code, line.raw_name),
                unit=line.unit,
                prev_volume=0.0,
                curr_volume=float(line.volume),
                prev_tariff=0.0,
                curr_tariff=float(line.tariff),
                prev_total=0.0,
                curr_total=float(line.total),
                delta_abs=float(line.total),
                delta_pct=0.0,
                tariff_delta_rub=0.0,
                volume_delta_rub=0.0,
                coeff_surcharge_rub=coeff_surcharge,
                status="warning" if has_coeff else "ok",
                plain_explanation=(
                    f"Строка «{line.raw_name}»: начислено {line.total:.2f} ₽ (первая квитанция в истории)."
                ),
            )
        )

    # 4. Factor breakdown is zeroed since there is no baseline period
    factor_breakdown = FactorBreakdown(
        tariff_effect_rub=0.0,
        volume_effect_rub=0.0,
        recalculation_effect_rub=0.0,
        new_services_effect_rub=0.0,
    )

    # 5. Check QR code if present
    qr_verified = True
    if curr_bill.qr_data:
        qr_sum = (
            curr_bill.qr_sum_rub
            if curr_bill.qr_sum_rub is not None
            else extract_sum_rub(curr_bill.qr_data)
        )
        if not verify_qr_sum(curr_bill.total_amount, qr_sum):
            qr_verified = False

    # 6. Build summary report
    summary = SummaryReport(
        prev_period="",
        curr_period=curr_bill.period,
        prev_total=0.0,
        curr_total=curr_bill.total_amount,
        delta_abs=curr_bill.total_amount,
        delta_pct=0.0,
        qr_verified=qr_verified,
        status_level="warning" if anomalies else "ok",
    )

    return ComparisonReport(
        comparison_id=f"cmp-{uuid.uuid4().hex}",
        summary=summary,
        factor_breakdown=factor_breakdown,
        anomalies=anomalies,
        items=items,
    )


def process_uploaded_bill(
    db: Session,
    curr_bill: BillDocument,
    user_id: str,
) -> ComparisonReport:
    """Process an uploaded utility bill for a given user.

    Steps:
    1. Persist the current bill associated with ``user_id``.
    2. Look up the most recent prior bill for the same user and address.
    3. If found: run two-receipt deterministic factor analysis.
       If not found: run single-bill normative audit.
    4. Save comparison report in database and in-memory cache with ``user_id``.
    5. Return the computed ``ComparisonReport``.
    """
    # Step 1: Save current bill in DB
    crud.save_bill(db, curr_bill, user_id=user_id)

    # Step 2: Find previous bill in DB with overlapping services
    curr_codes = [s.service_code for s in curr_bill.services]
    prev_bill_orm = crud.find_previous_bill(
        db,
        user_id=user_id,
        address=curr_bill.address,
        current_period=curr_bill.period,
        service_codes=curr_codes,
        provider_name=getattr(curr_bill, "provider_name", None),
    )

    # Step 3: Analyze
    if prev_bill_orm is not None:
        prev_doc = crud.bill_to_document(prev_bill_orm)
        report = analyze(prev_doc, curr_bill)
    else:
        prev_doc = None
        report = _run_normative_audit(curr_bill)

    # Step 4: Save comparison in DB and cache
    try:
        crud.save_comparison(
            db,
            report,
            prev_bill=prev_doc if prev_doc is not None else None,
            curr_bill=curr_bill,
            user_id=user_id,
        )
    except Exception as exc:
        db.rollback()
        logger.exception(f"Failed to persist comparison in database: {exc}")

    try:
        store_comparison(
            report.comparison_id,
            report,
            curr_bill,
            prev_doc if prev_doc is not None else curr_bill,
            owner_id=user_id,
        )
    except Exception as exc:
        logger.exception(f"Failed to store comparison in cache: {exc}")

    # Step 5: Return report
    return report


def get_user_history(db: Session, user_id: str) -> UserHistory:
    """Return all receipts and comparison reports for a user."""
    bills = crud.get_user_bills(db, user_id)
    comparisons = crud.get_user_comparisons(db, user_id)
    return UserHistory(bills=bills, comparisons=comparisons)


class ComparisonService:
    """Service wrapper for auto-comparison and history operations."""

    @staticmethod
    def process_uploaded_bill(
        db: Session,
        curr_bill: BillDocument,
        user_id: str,
    ) -> ComparisonReport:
        """Process an uploaded utility bill for a given user."""
        return process_uploaded_bill(db, curr_bill, user_id)

    @staticmethod
    def get_user_history(
        db: Session,
        user_id: str,
    ) -> UserHistory:
        """Return history for a user."""
        return get_user_history(db, user_id)
