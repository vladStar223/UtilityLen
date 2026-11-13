"""Table view component — 'Was / Now' breakdown of billing items."""
import pandas as pd
import streamlit as st


def render_items_table(items: list) -> None:
    """Render a detailed 'Was / Now' table for all billing line items."""
    st.markdown("### 📋 Детализация начислений по услугам («Было / Стало»)")

    if not items:
        return

    rows = []
    for item in items:
        rows.append(
            {
                "Услуга": item.get("display_name", ""),
                "Расход": (
                    f"{item.get('prev_volume', 0)} → "
                    f"{item.get('curr_volume', 0)} "
                    f"{item.get('unit', '')}"
                ),
                "Тариф": (
                    f"{item.get('prev_tariff', 0):,.2f} → "
                    f"{item.get('curr_tariff', 0):,.2f} ₽"
                ),
                "Итого": (
                    f"{item.get('prev_total', 0):,.2f} → "
                    f"{item.get('curr_total', 0):,.2f} ₽"
                ),
                "Дельта": (
                    f"{item.get('delta_abs', 0):+,.2f} ₽ "
                    f"({item.get('delta_pct', 0):+.1f}%)"
                ),
                "Пояснение на человеческом": item.get("plain_explanation", ""),
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
