"""SQLAlchemy 2.0 ORM models for the UtilityLens relational schema.

All monetary values are stored as ``Numeric`` (kopeck precision), volumes as
``Numeric``, and the free-form JSON documents (factor breakdown, summary,
tool calls) as portable ``JSON`` columns so the schema works identically on
SQLite (tests) and PostgreSQL (production).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    """A registered user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    first_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    personal_account: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    bills: Mapped[List["Bill"]] = relationship(back_populates="user")
    comparisons: Mapped[List["Comparison"]] = relationship(back_populates="user")



class Bill(Base):
    """A single utility receipt (квитанция)."""

    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    period: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(String)
    payer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    personal_account: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    qr_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    qr_sum_rub: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    qr_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    services: Mapped[List["BillService"]] = relationship(
        back_populates="bill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    meters: Mapped[List["MeterReading"]] = relationship(
        back_populates="bill",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="bills")


class BillService(Base):
    """A single accrual line (услуга) within a receipt."""

    __tablename__ = "bill_services"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[str] = mapped_column(
        ForeignKey("bills.bill_id", ondelete="CASCADE"),
        index=True,
    )
    service_code: Mapped[str] = mapped_column(String)
    raw_name: Mapped[str] = mapped_column(String)
    unit: Mapped[str] = mapped_column(String)
    volume: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    tariff: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    coefficient: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1.00"))
    recalculation: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    penalty: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))

    bill: Mapped["Bill"] = relationship(back_populates="services")


class MeterReading(Base):
    """An individual (ИПУ) meter reading attached to a receipt."""

    __tablename__ = "meter_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    bill_id: Mapped[str] = mapped_column(
        ForeignKey("bills.bill_id", ondelete="CASCADE"),
        index=True,
    )
    meter_id: Mapped[str] = mapped_column(String)
    service_code: Mapped[str] = mapped_column(String)
    prev_reading: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0"))
    current_reading: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    verification_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    bill: Mapped["Bill"] = relationship(back_populates="meters")


class Comparison(Base):
    """A factor-analysis report comparing two consecutive receipts."""

    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prev_bill_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    curr_bill_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    delta_abs: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    delta_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    status_level: Mapped[str] = mapped_column(String)
    factor_breakdown: Mapped[dict] = mapped_column(JSON)
    summary_data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    anomalies: Mapped[List["ComparisonAnomaly"]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="comparison",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    user: Mapped[Optional["User"]] = relationship(back_populates="comparisons")


class ComparisonAnomaly(Base):
    """An anomaly detected during the factor analysis."""

    __tablename__ = "comparison_anomalies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[str] = mapped_column(
        ForeignKey("comparisons.comparison_id", ondelete="CASCADE"),
        index=True,
    )
    code: Mapped[str] = mapped_column(String)
    severity: Mapped[str] = mapped_column(String)
    service_category: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    impact_rub: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    hint: Mapped[str] = mapped_column(Text)

    comparison: Mapped["Comparison"] = relationship(back_populates="anomalies")


class ChatMessage(Base):
    """A single chat turn in the AI-lawyer history."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    comparison_id: Mapped[str] = mapped_column(
        ForeignKey("comparisons.comparison_id", ondelete="CASCADE"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    comparison: Mapped["Comparison"] = relationship(back_populates="messages")
