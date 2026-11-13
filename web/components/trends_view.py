"""Trends view component — multi-line price dynamics chart."""
import streamlit as st
import plotly.graph_objects as go


def render_trends_view() -> None:
    """Render the full-screen price trends chart screen."""
    is_dark = st.session_state.get("theme_dark", True)
    text_color = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#475569"
    card_bg = "rgba(30, 41, 59, 0.85)" if is_dark else "rgba(255, 255, 255, 0.9)"
    card_border = "#334155" if is_dark else "rgba(203, 213, 225, 0.9)"
    grid_color = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(15, 23, 42, 0.08)"

    # --- Header ---
    col_title, col_badge, col_back = st.columns([4, 1.5, 1.5])
    with col_title:
        st.markdown("## 📈 Динамика изменения цен и тарифов")
    with col_badge:
        st.markdown(
            f"<div style='display:flex;align-items:center;height:100%;padding-top:12px;'>"
            f"<span style='background:{card_bg};color:{text_muted};border:1px solid {card_border};"
            f"border-radius:12px;padding:4px 14px;font-size:13px;font-weight:600;'>"
            f"Июнь — Ноябрь 2026</span></div>",
            unsafe_allow_html=True,
        )
    with col_back:
        if st.button("← Вернуться к квитанции", key="trends_back"):
            st.session_state["active_screen"] = "analysis"
            st.rerun()

    st.divider()

    # --- Tabs ---
    tab_trends, tab_waterfall = st.tabs(
        ["📈 Динамика тарифов (Мульти-линии)", "📊 Факторный водопад (Waterfall)"]
    )

    with tab_trends:
        # --- Data ---
        months = ["Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь"]

        data = {
            "🔥 Отопление": {
                "values": [800, 800, 800, 1200, 3640, 4223],
                "color": "#f59e0b",
            },
            "💧 Холодная вода (ХВС)": {
                "values": [310, 310, 315, 320, 324, 735.54],
                "color": "#0284c7" if not is_dark else "#38bdf8",
            },
            "♨️ Горячая вода (ГВС)": {
                "values": [950, 1035, 1035, 1040, 1040, 1094],
                "color": "#e11d48" if not is_dark else "#fb7185",
            },
            "⚡ Электричество": {
                "values": [1180, 1190, 1220, 1190, 1210, 1240],
                "color": "#059669" if not is_dark else "#34d399",
            },
        }

        # --- Filter ---
        selected = st.multiselect(
            "Выберите категории для отображения на графике:",
            list(data.keys()),
            default=list(data.keys()),
            key="trends_filter",
        )

        # --- Plotly Chart ---
        fig = go.Figure()

        for category in selected:
            entry = data[category]
            fig.add_trace(
                go.Scatter(
                    x=months,
                    y=entry["values"],
                    name=category,
                    mode="lines+markers",
                    line=dict(width=3, color=entry["color"]),
                    marker=dict(size=8, color=entry["color"]),
                    hovertemplate="%{y:,.2f} ₽<extra>" + category + "</extra>",
                )
            )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, Open Sans, sans-serif", color=text_color),
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
                font=dict(size=13, color=text_color),
            ),
            margin=dict(l=40, r=40, t=20, b=40),
            xaxis=dict(
                gridcolor=grid_color,
                linecolor=grid_color,
                tickfont=dict(size=13, color=text_color),
            ),
            yaxis=dict(
                gridcolor=grid_color,
                linecolor=grid_color,
                tickformat=",.0f",
                ticksuffix=" ₽",
                tickfont=dict(size=13, color=text_color),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)

    with tab_waterfall:
        # --- Extract data from session state ---
        analysis_result = st.session_state.get("analysis_result", {}) or {}
        summary = analysis_result.get("summary", {})
        factors = analysis_result.get("factor_breakdown", {})

        prev_total = summary.get("prev_total", 5420.0) or 0.0
        curr_total = summary.get("curr_total", 6890.5) or 0.0
        tar_eff = factors.get("tariff_effect_rub", 180.0) or 0.0
        vol_eff = factors.get("volume_effect_rub", 940.5) or 0.0
        recalc_eff = (
            (factors.get("recalculation_effect_rub", 350.0) or 0.0)
            + (factors.get("new_services_effect_rub", 0.0) or 0.0)
        )

        def _fmt_delta(val: float) -> str:
            sign = "+" if val > 0 else ""
            return f"{sign}{val:,.0f} ₽"

        # --- Waterfall chart ---
        fig_waterfall = go.Figure(
            go.Waterfall(
                name="Факторы",
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=[
                    "Счет прошлого мес.",
                    "Рост тарифов",
                    "Рост объема",
                    "Штрафы/Перерасчеты",
                    "Итог к оплате",
                ],
                textposition="outside",
                text=[
                    f"{prev_total:,.0f} ₽",
                    _fmt_delta(tar_eff),
                    _fmt_delta(vol_eff),
                    _fmt_delta(recalc_eff),
                    f"{curr_total:,.0f} ₽",
                ],
                y=[prev_total, tar_eff, vol_eff, recalc_eff, curr_total],
                connector={"line": {"color": "rgba(148, 163, 184, 0.5)"}},
                increasing={"marker": {"color": "#fb7185"}},
                decreasing={"marker": {"color": "#34d399"}},
                totals={"marker": {"color": "#7c3aed"}},
            )
        )

        fig_waterfall.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Open Sans, Inter, sans-serif", color=text_color),
            margin=dict(l=40, r=40, t=40, b=40),
            xaxis=dict(
                gridcolor=grid_color,
                linecolor=grid_color,
                tickfont=dict(size=13, color=text_color),
            ),
            yaxis=dict(
                gridcolor=grid_color,
                linecolor=grid_color,
                tickformat=",.0f",
                ticksuffix=" ₽",
                tickfont=dict(size=13, color=text_color),
            ),
        )

        st.plotly_chart(fig_waterfall, use_container_width=True)
        st.caption(
            "Диаграмма декомпозирует общую переплату на математические составляющие"
            " без участия LLM."
        )

    # --- Trend Cards ---
    st.markdown("### Ключевые тренды")
    c1, c2, c3, c4 = st.columns(4)

    card_style = (
        f"background:{card_bg};border-radius:16px;padding:18px 16px;"
        f"border:1px solid {card_border};height:100%;box-shadow: 0 4px 12px rgba(0,0,0,0.05);"
    )

    with c1:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<p style='color:#f59e0b;font-size:18px;font-weight:700;margin:0;'>🔥 Отопление</p>"
            f"<p style='color:{text_color};font-size:26px;font-weight:800;margin:6px 0 2px;'>+38%</p>"
            f"<p style='color:{text_muted};font-size:13px;margin:0;'>в ноябре (морозы)</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<p style='color:#0284c7;font-size:18px;font-weight:700;margin:0;'>💧 Холодная вода</p>"
            f"<p style='color:#e11d48;font-size:26px;font-weight:800;margin:6px 0 2px;'>+127%</p>"
            f"<p style='color:{text_muted};font-size:13px;margin:0;'>включен коэфф. 1.5!</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<p style='color:#e11d48;font-size:18px;font-weight:700;margin:0;'>♨️ Горячая вода</p>"
            f"<p style='color:{text_color};font-size:26px;font-weight:800;margin:6px 0 2px;'>+9%</p>"
            f"<p style='color:{text_muted};font-size:13px;margin:0;'>индексация с июля</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"<div style='{card_style}'>"
            f"<p style='color:#059669;font-size:18px;font-weight:700;margin:0;'>⚡ Электричество</p>"
            f"<p style='color:{text_color};font-size:26px;font-weight:800;margin:6px 0 2px;'>±3%</p>"
            f"<p style='color:{text_muted};font-size:13px;margin:0;'>норматив стабилен</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
