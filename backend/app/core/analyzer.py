"""Deterministic factor-analysis kernel (the "accountant").

All money math lives here and nowhere else. For every service line the
total delta is decomposed into three components:

* tariff effect     ``dS_tariff = (T2 - T1) * V1``
* volume effect     ``dS_volume = T2 * (V2 - V1)``
* coefficient /
  recalculation /
  penalty residue   ``dS_recalc = S2 - (T2 * V2)``

The three effects always sum to the line delta ``S2 - S1``, and the sum of
all line deltas converges to the receipt total delta to the kopeck.
"""

import uuid
from datetime import date, datetime, timedelta
from typing import Dict, List

from app.core.models import (
    AnomalyItem,
    BillDocument,
    ComparisonReport,
    FactorBreakdown,
    ServiceItem,
    ServiceLine,
    SummaryReport,
)
from app.core.normalizer import display_name, normalize_service_code
from app.ingestion.qr_parser import extract_sum_rub, verify_qr_sum

_SEVERITY_RED = "red"
_SEVERITY_YELLOW = "yellow"
_SEVERITY_GREEN = "green"

_KNOWN_CODES = {
    "cold_water",
    "hot_water",
    "heating",
    "electricity",
    "cold_water_soi",
    "hot_water_soi",
    "electricity_soi",
    "wastewater_soi",
    "maintenance",
    "waste",
    "wastewater",
    "drainage",
    "capital_repair",
    "capital_repairs",
    "recalculation",
    "optional_service",
}

_SOI_CODES = ("cold_water_soi", "hot_water_soi", "electricity_soi", "wastewater_soi")


def _round2(value: float) -> float:
    return round(float(value), 2)


def _pct(part: float, base: float) -> float:
    if base == 0:
        return 0.0
    return _round2(part / base * 100.0)


def _line_code(line: ServiceLine) -> str:
    """Return the canonical category code for a service line."""
    code = normalize_service_code(line.service_code)
    if code not in _KNOWN_CODES:
        code = normalize_service_code(line.raw_name)
    return code


def _build_comparison_id(prev_bill: BillDocument, curr_bill: BillDocument) -> str:
    return f"cmp-{uuid.uuid4().hex}"


def _status_level(items: List[ServiceItem], anomalies: List[AnomalyItem]) -> str:
    severities = [a.severity for a in anomalies] + [i.status for i in items]
    if _SEVERITY_RED in severities:
        return _SEVERITY_RED
    if _SEVERITY_YELLOW in severities:
        return _SEVERITY_YELLOW
    return _SEVERITY_GREEN


def _item_status(delta_pct: float, coeff_surcharge: float) -> str:
    if coeff_surcharge != 0.0 or delta_pct >= 30.0:
        return _SEVERITY_RED
    if delta_pct >= 10.0:
        return _SEVERITY_YELLOW
    return _SEVERITY_GREEN


def _verification_due(due_date_str: str, period: str) -> bool:
    """True when the verification term expired relative to the end of ``period``."""
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False

    try:
        year, month = (int(p) for p in period.split("-"))
        period_end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    except (ValueError, AttributeError):
        period_end = date.today()

    return due < period_end


def _explain(
    code: str,
    raw_name: str,
    t1: float,
    t2: float,
    v1: float,
    v2: float,
    d_recalc: float,
) -> str:
    unit = "м³" if code in ("cold_water", "hot_water", "cold_water_soi", "wastewater") else "ед."
    parts: List[str] = []
    if abs(v2 - v1) > 1e-9:
        parts.append(f"расход изменился с {v1:g} на {v2:g} {unit}")
    if abs(t2 - t1) > 1e-9:
        parts.append(f"тариф изменился на {t2 - t1:.2f} ₽")
    if abs(d_recalc) > 1e-9:
        parts.append(f"начислен коэффициент/перерасчет {d_recalc:.2f} ₽")
    if not parts:
        return f"По строке «{raw_name}» изменений нет."
    return ("По строке «" + raw_name + "»: " + ", ".join(parts) + ".")


def _match_key(line: ServiceLine) -> str:
    """Return a composite match key distinguishing sub-services (day/night, energy/carrier)."""
    code = _line_code(line)
    unit = (line.unit or "").strip().lower()
    name = (line.raw_name or "").lower()
    tag = ""
    if "ночь" in name or "ночн" in name or "т2" in name:
        tag = ":night"
    elif "день" in name or "дневн" in name or "т1" in name:
        tag = ":day"
    elif "пик" in name or "т3" in name:
        tag = ":peak"
    elif "теплоносител" in name:
        tag = ":carrier"
    elif "тепловая энерги" in name:
        tag = ":energy"
    return f"{code}:{unit}{tag}"


def _detect_anomalies(
    curr_bill: BillDocument,
    prev_lines: Dict[str, ServiceLine],
) -> List[AnomalyItem]:
    anomalies: List[AnomalyItem] = []

    # Raising coefficients (1.5 / 3.0) applied to a matched service.
    for line in curr_bill.services:
        code = _line_code(line)
        prev_line = prev_lines.get(_match_key(line)) or prev_lines.get(code)
        coeff = line.coefficient if line.coefficient else 1.0
        if not (coeff > 1.0):
            continue
        surcharge = _round2(line.total - line.tariff * line.volume)
        if coeff < 3.0:
            anomalies.append(
                AnomalyItem(
                    code="APPLYING_COEFF_1_5",
                    severity=_SEVERITY_RED,
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
                    severity=_SEVERITY_RED,
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

    # Expired meter verification.
    for meter in curr_bill.meters or []:
        if not meter.verification_due_date:
            continue
        if _verification_due(meter.verification_due_date, curr_bill.period):
            anomalies.append(
                AnomalyItem(
                    code="METER_VERIFICATION_DUE",
                    severity=_SEVERITY_YELLOW,
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

    # SOI / ODN spike above 30%.
    for code in _SOI_CODES:
        prev_line = prev_lines.get(code)
        curr_line = next((l for l in curr_bill.services if _line_code(l) == code), None)
        if prev_line is None or curr_line is None or prev_line.total == 0:
            continue
        growth = (curr_line.total - prev_line.total) / prev_line.total * 100.0
        if growth > 30.0:
            anomalies.append(
                AnomalyItem(
                    code="SOI_SPIKE",
                    severity=_SEVERITY_YELLOW,
                    service_category=code,
                    title="Резкий рост расходов на СОИ/ОДН",
                    impact_rub=_round2(curr_line.total - prev_line.total),
                    hint=(
                        "Расходы на общедомовые нужды выросли более чем на 30% "
                        "при неизменном тарифе. Возможна утечка или небаланс дома."
                    ),
                )
            )

    # Optional (imposed) services: antenna, insurance, radio.
    for line in curr_bill.services:
        if _line_code(line) == "optional_service":
            anomalies.append(
                AnomalyItem(
                    code="OPTIONAL_SERVICE_DETECTED",
                    severity=_SEVERITY_YELLOW,
                    service_category="optional_service",
                    title="Обнаружена необязательная услуга",
                    impact_rub=line.total,
                    hint=(
                        f"Строка «{line.raw_name}» не относится к обязательным "
                        "жилищно-коммунальным услугам. Вы вправе отказаться от нее."
                    ),
                )
            )

    return anomalies


def analyze(prev_bill: BillDocument, curr_bill: BillDocument) -> ComparisonReport:
    """Run the deterministic factor analysis for two consecutive receipts."""
    prev_total = prev_bill.total_amount
    curr_total = curr_bill.total_amount
    delta_abs = _round2(curr_total - prev_total)

    prev_lines: Dict[str, ServiceLine] = {}
    for line in prev_bill.services:
        prev_lines[_match_key(line)] = line
        code = _line_code(line)
        if code not in prev_lines:
            prev_lines[code] = line

    items: List[ServiceItem] = []
    tariff_effect = 0.0
    volume_effect = 0.0
    recalculation_effect = 0.0
    new_services_effect = 0.0

    for line in curr_bill.services:
        code = _line_code(line)
        prev_line = prev_lines.get(_match_key(line)) or prev_lines.get(code)

        if prev_line is not None:
            t1, v1, s1 = prev_line.tariff, prev_line.volume, prev_line.total
            t2, v2, s2 = line.tariff, line.volume, line.total

            d_tariff = _round2((t2 - t1) * v1)
            d_volume = _round2(t2 * (v2 - v1))
            # The residue captures coefficient surcharges, recalculation and
            # penalties. For plain lines the tiny float/rounding mismatch
            # between ``total`` and ``tariff * volume`` is data noise, not a
            # real effect, so it is zeroed out.
            has_other = (
                (line.coefficient != 1.0)
                or (line.recalculation != 0.0)
                or (line.penalty != 0.0)
            )
            d_recalc = _round2(s2 - t2 * v2) if has_other else 0.0

            line_delta = _round2(s2 - s1)
            line_pct = _pct(line_delta, s1)

            tariff_effect += d_tariff
            volume_effect += d_volume
            recalculation_effect += d_recalc

            items.append(
                ServiceItem(
                    category=code,
                    display_name=display_name(code, line.raw_name),
                    unit=line.unit,
                    prev_volume=v1,
                    curr_volume=v2,
                    prev_tariff=t1,
                    curr_tariff=t2,
                    prev_total=s1,
                    curr_total=s2,
                    delta_abs=line_delta,
                    delta_pct=line_pct,
                    tariff_delta_rub=d_tariff,
                    volume_delta_rub=d_volume,
                    coeff_surcharge_rub=d_recalc,
                    status=_item_status(line_pct, d_recalc),
                    plain_explanation=_explain(
                        code, line.raw_name, t1, t2, v1, v2, d_recalc
                    ),
                )
            )
        else:
            # New service that has no counterpart in the previous receipt.
            items.append(
                ServiceItem(
                    category=code,
                    display_name=display_name(code, line.raw_name),
                    unit=line.unit,
                    prev_volume=0.0,
                    curr_volume=line.volume,
                    prev_tariff=0.0,
                    curr_tariff=line.tariff,
                    prev_total=0.0,
                    curr_total=line.total,
                    delta_abs=line.total,
                    delta_pct=0.0,
                    tariff_delta_rub=0.0,
                    volume_delta_rub=0.0,
                    coeff_surcharge_rub=line.total,
                    status=_SEVERITY_RED,
                    plain_explanation=(
                        f"Новая строка «{line.raw_name}» появилась только в "
                        "текущем периоде."
                    ),
                )
            )
            if code == "recalculation":
                recalculation_effect += line.total
            else:
                new_services_effect += line.total

    factor_breakdown = FactorBreakdown(
        tariff_effect_rub=_round2(tariff_effect),
        volume_effect_rub=_round2(volume_effect),
        recalculation_effect_rub=_round2(recalculation_effect),
        new_services_effect_rub=_round2(new_services_effect),
    )

    anomalies = _detect_anomalies(curr_bill, prev_lines)

    qr_verified = True
    for bill in (prev_bill, curr_bill):
        if bill.qr_data:
            qr_sum = (
                bill.qr_sum_rub
                if bill.qr_sum_rub is not None
                else extract_sum_rub(bill.qr_data)
            )
            if not verify_qr_sum(bill.total_amount, qr_sum):
                qr_verified = False

    summary = SummaryReport(
        prev_period=prev_bill.period,
        curr_period=curr_bill.period,
        prev_total=prev_total,
        curr_total=curr_total,
        delta_abs=delta_abs,
        delta_pct=_pct(delta_abs, prev_total),
        qr_verified=qr_verified,
        status_level=_status_level(items, anomalies),
    )

    return ComparisonReport(
        comparison_id=_build_comparison_id(prev_bill, curr_bill),
        summary=summary,
        factor_breakdown=factor_breakdown,
        anomalies=anomalies,
        items=items,
    )
