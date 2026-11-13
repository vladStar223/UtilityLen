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
    service_code: str = Field(description="Код услуги (например, 'cold_water', 'heating')", examples=["cold_water", "heating", "electricity"])
    raw_name: str = Field(description="Исходное название услуги из квитанции", examples=["Холодное водоснабжение", "Отопление"])
    unit: str = Field(description="Единица измерения услуги", examples=["м3", "Гкал", "кВт·ч"])
    volume: float = Field(description="Объём потребления за период", examples=[12.5, 1.8, 250.0])
    tariff: Money = Field(description="Тариф за единицу, руб.", examples=[45.50, 2150.00, 5.20])
    coefficient: float = Field(default=1.0, description="Коэффициент (например, повышающий)", examples=[1.0, 1.5])
    recalculation: Money = Field(default=0.0, description="Перерасчёт, руб.", examples=[0.0, -150.50, 200.00])
    penalty: Money = Field(default=0.0, description="Пени, руб.", examples=[0.0, 25.30])
    total: Money = Field(description="Итого по строке, руб.", examples=[568.75, 3870.00, 1300.00])


class MeterReading(BaseModel):
    meter_id: str = Field(description="Идентификатор прибора учёта", examples=["CW-001", "HW-002", "EL-003"])
    service_code: str = Field(description="Код услуги, к которой относится прибор", examples=["cold_water", "hot_water"])
    current_reading: float = Field(description="Текущее показание счётчика", examples=[125.5, 340.0])
    prev_reading: Optional[float] = Field(default=None, description="Предыдущее показание счётчика", examples=[110.2, 325.0])
    verification_due_date: Optional[str] = Field(default=None, description="Дата следующей поверки (YYYY-MM-DD)", examples=["2027-06-01"])


class BillDocument(BaseModel):
    bill_id: str = Field(description="Уникальный идентификатор квитанции", examples=["bill-2024-01-001"])
    period: str = Field(description="Расчётный период (YYYY-MM)", examples=["2024-01", "2024-02"])
    address: str = Field(description="Адрес объекта", examples=["г. Владивосток, ул. Ленина, д. 10, кв. 25"])
    payer: Optional[str] = Field(default=None, description="ФИО плательщика", examples=["Иванов Иван Иванович"])
    total_amount: Money = Field(description="Общая сумма к оплате, руб.", examples=[4520.75, 6800.00])
    qr_data: Optional[str] = Field(default=None, description="Данные QR-кода квитанции", examples=["01;1234567890;..."])
    qr_sum_rub: Optional[Money] = Field(default=None, description="Сумма из QR-кода, руб.", examples=[4520.75])
    meters: Optional[List[MeterReading]] = Field(default_factory=list, description="Показания приборов учёта")
    services: List[ServiceLine] = Field(description="Список услуг в квитанции")


class SummaryReport(BaseModel):
    prev_period: str = Field(description="Предыдущий период (YYYY-MM)", examples=["2024-01"])
    curr_period: str = Field(description="Текущий период (YYYY-MM)", examples=["2024-02"])
    prev_total: Money = Field(description="Итого за предыдущий период, руб.", examples=[4200.50])
    curr_total: Money = Field(description="Итого за текущий период, руб.", examples=[4520.75])
    delta_abs: Money = Field(description="Абсолютное изменение, руб.", examples=[320.25, -150.00])
    delta_pct: float = Field(description="Относительное изменение, %", examples=[7.62, -3.50])
    qr_verified: bool = Field(description="QR-код успешно верифицирован", examples=[True, False])
    status_level: str = Field(description="Уровень статуса (ok, warning, critical)", examples=["ok", "warning", "critical"])


class FactorBreakdown(BaseModel):
    tariff_effect_rub: Money = Field(description="Вклад изменения тарифов, руб.", examples=[150.50, -20.00])
    volume_effect_rub: Money = Field(description="Вклад изменения объёмов, руб.", examples=[200.00, -80.50])
    recalculation_effect_rub: Money = Field(description="Вклад перерасчётов, руб.", examples=[-100.00, 50.00])
    new_services_effect_rub: Money = Field(description="Вклад новых услуг, руб.", examples=[70.25, 0.0])


class AnomalyItem(BaseModel):
    code: str = Field(description="Код аномалии", examples=["TARIFF_SPIKE", "VOLUME_ANOMALY", "NEW_SERVICE"])
    severity: str = Field(description="Уровень серьёзности (info, warning, error)", examples=["info", "warning", "error"])
    service_category: str = Field(description="Категория услуги", examples=["water", "heating", "electricity"])
    title: str = Field(description="Заголовок аномалии", examples=["Резкий рост тарифа на отопление"])
    impact_rub: Money = Field(description="Финансовое влияние, руб.", examples=[250.50, -100.00])
    hint: str = Field(description="Рекомендация для пользователя", examples=["Проверьте обоснованность повышения тарифа"])


class ServiceItem(BaseModel):
    category: str = Field(description="Категория услуги", examples=["water", "heating", "electricity", "maintenance"])
    display_name: str = Field(description="Отображаемое название услуги", examples=["Холодное водоснабжение", "Отопление"])
    unit: str = Field(description="Единица измерения", examples=["м3", "Гкал", "кВт·ч"])
    prev_volume: float = Field(description="Объём за предыдущий период", examples=[10.5, 1.5])
    curr_volume: float = Field(description="Объём за текущий период", examples=[12.5, 1.8])
    prev_tariff: Money = Field(description="Тариф за предыдущий период, руб.", examples=[42.00, 2050.00])
    curr_tariff: Money = Field(description="Тариф за текущий период, руб.", examples=[45.50, 2150.00])
    prev_total: Money = Field(description="Итого за предыдущий период, руб.", examples=[441.00, 3075.00])
    curr_total: Money = Field(description="Итого за текущий период, руб.", examples=[568.75, 3870.00])
    delta_abs: Money = Field(description="Абсолютное изменение, руб.", examples=[127.75, 795.00])
    delta_pct: float = Field(description="Относительное изменение, %", examples=[28.97, 25.85])
    tariff_delta_rub: Money = Field(description="Вклад изменения тарифа, руб.", examples=[43.75, 150.00])
    volume_delta_rub: Money = Field(description="Вклад изменения объёма, руб.", examples=[84.00, 645.00])
    coeff_surcharge_rub: Money = Field(description="Надбавка за коэффициент, руб.", examples=[0.0, 50.00])
    status: str = Field(description="Статус услуги (ok, warning, error)", examples=["ok", "warning", "error"])
    plain_explanation: str = Field(description="Простое объяснение изменений для пользователя", examples=["Тариф вырос на 8.3%, потребление увеличилось на 19%"])


class ComparisonReport(BaseModel):
    comparison_id: str = Field(description="Уникальный идентификатор сравнения", examples=["cmp-20240215-abc123"])
    summary: SummaryReport = Field(description="Сводка по сравнению")
    factor_breakdown: FactorBreakdown = Field(description="Факторный разбор изменений")
    anomalies: List[AnomalyItem] = Field(description="Список обнаруженных аномалий")
    items: List[ServiceItem] = Field(description="Детализация по каждой услуге")
