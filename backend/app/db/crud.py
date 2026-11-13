"""CRUD operations mapping the Pydantic domain models to the ORM tables."""

import re
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.auth import hash_password
from app.core.logging import logger
from app.core.models import BillDocument, ComparisonReport
from app.db.models import (
    Bill,
    BillService,
    ChatMessage,
    Comparison,
    ComparisonAnomaly,
    MeterReading,
    User,
)
from app.ingestion.qr_parser import extract_sum_rub, verify_qr_sum


def _dec(value: Optional[float], default: str = "0") -> Decimal:
    """Coerce an optional float to a ``Decimal`` (falling back to ``default``)."""
    if value is None:
        return Decimal(default)
    return Decimal(str(value))


_PERSONAL_ACC_RE = re.compile(r"(PersonalAcc=\d{4})\d+(\d{4})")


def mask_qr_personal_data(qr_raw: str) -> str:
    """Mask the ``PersonalAcc`` (личный счёт) inside a ГОСТ Р 56042-2014 QR string.

    Per 152-ФЗ the personal account number is personal data: only the first
    four and last four digits are kept, the middle is replaced with ``****``.
    """
    if not qr_raw:
        return qr_raw
    return _PERSONAL_ACC_RE.sub(r"\1****\2", qr_raw)


def save_bill(db: Session, bill_doc: BillDocument, user_id: Optional[str] = None) -> Bill:
    """Persist a receipt together with its services and meter readings.

    Idempotent: an existing receipt with the same ``bill_id`` is returned
    unchanged instead of being duplicated.
    """
    existing = db.query(Bill).filter(Bill.bill_id == bill_doc.bill_id).first()
    if existing is not None:
        if user_id and not existing.user_id:
            existing.user_id = user_id
            db.commit()
            db.refresh(existing)
        return existing

    qr_sum = bill_doc.qr_sum_rub
    if bill_doc.qr_data and qr_sum is None:
        qr_sum = extract_sum_rub(bill_doc.qr_data)
    qr_verified = bool(bill_doc.qr_data) and verify_qr_sum(bill_doc.total_amount, qr_sum)

    bill = Bill(
        bill_id=bill_doc.bill_id,
        user_id=user_id,
        period=bill_doc.period,
        address=bill_doc.address,
        payer=bill_doc.payer,
        total_amount=_dec(bill_doc.total_amount),
        qr_data=mask_qr_personal_data(bill_doc.qr_data)
        if bill_doc.qr_data
        else None,
        qr_sum_rub=_dec(qr_sum) if qr_sum is not None else None,
        qr_verified=qr_verified,
    )

    for line in bill_doc.services:
        bill.services.append(
            BillService(
                bill_id=bill_doc.bill_id,
                service_code=line.service_code,
                raw_name=line.raw_name,
                unit=line.unit,
                volume=_dec(line.volume, "0"),
                tariff=_dec(line.tariff, "0"),
                total=_dec(line.total, "0"),
                coefficient=_dec(line.coefficient, "1"),
            )
        )

    for meter in bill_doc.meters or []:
        bill.meters.append(
            MeterReading(
                bill_id=bill_doc.bill_id,
                meter_id=meter.meter_id,
                service_code=meter.service_code,
                prev_reading=_dec(meter.prev_reading, "0"),
                current_reading=_dec(meter.current_reading, "0"),
                verification_due_date=(
                    date.fromisoformat(meter.verification_due_date)
                    if meter.verification_due_date
                    else None
                ),
            )
        )

    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def get_bill(db: Session, bill_id: str) -> Optional[Bill]:
    """Return a persisted receipt by ``bill_id`` (or ``None``)."""
    return db.query(Bill).filter(Bill.bill_id == bill_id).first()


def save_comparison(
    db: Session,
    report: ComparisonReport,
    prev_bill: Optional[BillDocument],
    curr_bill: Optional[BillDocument],
    user_id: Optional[str] = None,
) -> Comparison:
    """Persist a factor-analysis report and its anomalies.

    The referenced receipts are saved first (idempotently) so the report
    remains self-contained. Re-saving the same ``comparison_id`` is a no-op.
    """
    if prev_bill is not None:
        save_bill(db, prev_bill, user_id=user_id)
    if curr_bill is not None:
        save_bill(db, curr_bill, user_id=user_id)

    existing = (
        db.query(Comparison)
        .filter(Comparison.comparison_id == report.comparison_id)
        .first()
    )
    if existing is not None:
        if user_id and not existing.user_id:
            existing.user_id = user_id
            db.commit()
            db.refresh(existing)
        return existing

    comparison = Comparison(
        comparison_id=report.comparison_id,
        user_id=user_id,
        prev_bill_id=prev_bill.bill_id if prev_bill else None,
        curr_bill_id=curr_bill.bill_id if curr_bill else None,
        delta_abs=_dec(report.summary.delta_abs),
        delta_pct=_dec(report.summary.delta_pct),
        status_level=report.summary.status_level,
        factor_breakdown=report.factor_breakdown.model_dump(mode="json"),
        summary_data=report.summary.model_dump(mode="json"),
    )

    for anomaly in report.anomalies:
        comparison.anomalies.append(
            ComparisonAnomaly(
                code=anomaly.code,
                severity=anomaly.severity,
                service_category=anomaly.service_category,
                title=anomaly.title,
                impact_rub=_dec(anomaly.impact_rub),
                hint=anomaly.hint,
            )
        )

    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison


def get_comparison(db: Session, comparison_id: str) -> Optional[Comparison]:
    """Return a persisted report by ``comparison_id`` (or ``None``).

    Callers should fall back to the cache layer (``app.core.cache``) when
    this returns ``None``.
    """
    return (
        db.query(Comparison)
        .filter(Comparison.comparison_id == comparison_id)
        .first()
    )


def save_chat_message(
    db: Session,
    comparison_id: str,
    role: str,
    content: str,
    tool_calls: Optional[dict] = None,
) -> ChatMessage:
    """Append a chat turn to the persisted history."""
    message = ChatMessage(
        comparison_id=comparison_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_chat_history(db: Session, comparison_id: str) -> List[ChatMessage]:
    """Return the chat history for a report, oldest first."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.comparison_id == comparison_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )


# =============================================================================
# User operations
# =============================================================================

def get_user_by_id(db: Session, id: int) -> Optional[User]:
    """Return a user by primary key ID (or None)."""
    return db.query(User).filter(User.id == id).first()


def get_user_by_user_id(db: Session, user_id: str) -> Optional[User]:
    """Return a user by unique user_id (or None)."""
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Return a user by email address (case-insensitive lookup, or None)."""
    return db.query(User).filter(User.email == email.strip().lower()).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Return a user by username (or None)."""
    return db.query(User).filter(User.username == username.strip()).first()


def create_user(
    db: Session,
    username: str,
    email: str,
    password: str,
    user_id: Optional[str] = None,
) -> User:
    """Create and persist a new user account with hashed password."""
    if not user_id:
        user_id = f"user_{uuid.uuid4().hex[:12]}"

    hashed = hash_password(password)
    user = User(
        user_id=user_id,
        username=username.strip(),
        email=email.strip().lower(),
        hashed_password=hashed,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_bills(db: Session, user_id: str) -> List[Bill]:
    """Return all receipts associated with a specific user, newest first."""
    return (
        db.query(Bill)
        .filter(Bill.user_id == user_id)
        .order_by(Bill.created_at.desc())
        .all()
    )


def get_user_comparisons(db: Session, user_id: str) -> List[Comparison]:
    """Return all comparison reports associated with a specific user, newest first."""
    return (
        db.query(Comparison)
        .filter(Comparison.user_id == user_id)
        .order_by(Comparison.created_at.desc())
        .all()
    )
