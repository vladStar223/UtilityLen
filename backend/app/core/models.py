"""Pydantic v2 domain models for UtilityLens.

Field names and shapes are frozen by ``contracts/bill_schema.json`` and
``contracts/compare_response.json``. Monetary values are protected by a
validator that rounds every money amount to two decimal places to guard
against floating point drift.
"""

from typing import Annotated, List, Optional

from pydantic import AfterValidator, BaseModel, Field


def _round_money(value: float) -> float:
    """Round a monetary value to two decimal places (kopeck precision)."""
    return round(float(value), 2)


#: Monetary amount, always rounded to two decimals.
Money = Annotated[float, AfterValidator(_round_money)]


class ServiceLine(BaseModel):
    service_code: str
    raw_name: str
    unit: str
    volume: float
    tariff: Money
    coefficient: float = 1.0
    recalculation: Money = 0.0
    penalty: Money = 0.0
    total: Money


class MeterReading(BaseModel):
    meter_id: str
    service_code: str
    current_reading: float
    prev_reading: Optional[float] = None
    verification_due_date: Optional[str] = None


class BillDocument(BaseModel):
    bill_id: str
    period: str
    address: str
    payer: Optional[str] = None
    total_amount: Money
    qr_data: Optional[str] = None
    qr_sum_rub: Optional[Money] = None
    meters: Optional[List[MeterReading]] = Field(default_factory=list)
    services: List[ServiceLine]


class SummaryReport(BaseModel):
    prev_period: str
    curr_period: str
    prev_total: Money
    curr_total: Money
    delta_abs: Money
    delta_pct: float
    qr_verified: bool
    status_level: str


class FactorBreakdown(BaseModel):
    tariff_effect_rub: Money
    volume_effect_rub: Money
    recalculation_effect_rub: Money
    new_services_effect_rub: Money


class AnomalyItem(BaseModel):
    code: str
    severity: str
    service_category: str
    title: str
    impact_rub: Money
    hint: str


class ServiceItem(BaseModel):
    category: str
    display_name: str
    unit: str
    prev_volume: float
    curr_volume: float
    prev_tariff: Money
    curr_tariff: Money
    prev_total: Money
    curr_total: Money
    delta_abs: Money
    delta_pct: float
    tariff_delta_rub: Money
    volume_delta_rub: Money
    coeff_surcharge_rub: Money
    status: str
    plain_explanation: str


class ComparisonReport(BaseModel):
    comparison_id: str
    summary: SummaryReport
    factor_breakdown: FactorBreakdown
    anomalies: List[AnomalyItem]
    items: List[ServiceItem]
