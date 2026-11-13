"""KPI summary cards component."""
import streamlit as st


def render_kpi_cards(summary: dict, factor_breakdown: dict):
    """Render the traffic-light KPI cards and QR verification badge."""
    st.subheader("📊 Сводка начислений")

    col1, col2, col3, col4 = st.columns(4)

    prev_p = summary.get("prev_period", "Октябрь")
    curr_p = summary.get("curr_period", "Ноябрь")

    col1.metric(
        f"Предыдущий период ({prev_p})",
        f"{summary.get('prev_total', 0):,.2f} ₽",
    )
    col2.metric(
        f"Текущий период ({curr_p})",
        f"{summary.get('curr_total', 0):,.2f} ₽",
    )

    delta_abs = summary.get("delta_abs", 0)
    delta_pct = summary.get("delta_pct", 0)
    col3.metric(
        "Разница к оплате",
        f"{delta_abs:+,.2f} ₽",
        f"{delta_pct:+.1f}%",
        delta_color="inverse",
    )

    effects = {
        "Объем потребления": factor_breakdown.get("volume_effect_rub", 0.0) or 0.0,
        "Рост тарифа": factor_breakdown.get("tariff_effect_rub", 0.0) or 0.0,
        "Перерасчет": factor_breakdown.get("recalculation_effect_rub", 0.0) or 0.0,
        "Новые услуги": factor_breakdown.get("new_services_effect_rub", 0.0) or 0.0,
    }
    top_factor, top_value = max(effects.items(), key=lambda x: abs(x[1])) if any(effects.values()) else ("Без изменений", 0.0)
    col4.metric("Главный драйвер роста", top_factor, f"{top_value:+,.2f} ₽", delta_color="inverse")

    if summary.get("qr_verified", False):
        st.success("🛡 **Верифицировано по ГОСТ QR:** Начисления соответствуют банковскому платежному коду")
    else:
        st.warning("⚠️ **Внимание:** Обнаружено расхождение с суммой банковского QR-кода")
