"""Trends view component — multi-line price dynamics chart."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render_trends_view() -> None:
    """Render the full-screen price trends chart screen."""

    # --- Header ---
    col_title, col_badge, col_back = st.columns([4, 1.5, 1.5])
    with col_title:
        st.markdown("## 📈 Динамика изменения цен и тарифов")
    with col_badge:
        st.markdown(
            "<div style='display:flex;align-items:center;height:100%;padding-top:12px;'>"
            "<span style='background:#334155;color:#94a3b8;border-radius:12px;"
            "padding:4px 14px;font-size:13px;font-weight:600;'>"
            "Июнь — Ноябрь 2026</span></div>",
            unsafe_allow_html=True,
        )
    with col_back:
        if st.button("← Вернуться к квитанции", key="trends_back"):
            st.session_state["active_screen"] = "analysis"
            st.rerun()

    st.divider()

    # --- Data ---
    months = ["Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь"]

    data = {
        "🔥 Отопление": {
            "values": [800, 800, 800, 1200, 3640, 4223],
            "color": "#fbbf24",
        },
        "💧 Холодная вода (ХВС)": {
            "values": [310, 310, 315, 320, 324, 735.54],
            "color": "#38bdf8",
        },
        "♨️ Горячая вода (ГВС)": {
            "values": [950, 1035, 1035, 1040, 1040, 1094],
            "color": "#fb7185",
        },
        "⚡ Электричество": {
            "values": [1180, 1190, 1220, 1190, 1210, 1240],
            "color": "#34d399",
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
        font=dict(family="Inter, Open Sans, sans-serif", color="#e2e8f0"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=13),
        ),
        margin=dict(l=40, r=40, t=20, b=40),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="rgba(255,255,255,0.15)",
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.08)",
            linecolor="rgba(255,255,255,0.15)",
            tickformat=",.0f",
            ticksuffix=" ₽",
            tickfont=dict(size=13),
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- Trend Cards ---
    st.markdown("### Ключевые тренды")
    c1, c2, c3, c4 = st.columns(4)

    card_style = (
        "background:#1e293b;border-radius:12px;padding:18px 16px;"
        "border:1px solid #334155;height:100%;"
    )

    with c1:
        st.markdown(
            f"<div style='{card_style}'>"
            "<p style='color:#fbbf24;font-size:22px;margin:0;'>🔥 Отопление</p>"
            "<p style='color:#f8fafc;font-size:28px;font-weight:700;margin:8px 0 4px;'>+38%</p>"
            "<p style='color:#94a3b8;font-size:13px;margin:0;'>в ноябре (морозы)</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"<div style='{card_style}'>"
            "<p style='color:#38bdf8;font-size:22px;margin:0;'>💧 Холодная вода</p>"
            "<p style='color:#f8fafc;font-size:28px;font-weight:700;margin:8px 0 4px;'>+127%</p>"
            "<p style='color:#94a3b8;font-size:13px;margin:0;'>включен коэфф. 1.5!</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"<div style='{card_style}'>"
            "<p style='color:#fb7185;font-size:22px;margin:0;'>♨️ Горячая вода</p>"
            "<p style='color:#f8fafc;font-size:28px;font-weight:700;margin:8px 0 4px;'>+9%</p>"
            "<p style='color:#94a3b8;font-size:13px;margin:0;'>плановая индексация с июля</p>"
            "</div>",
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"<div style='{card_style}'>"
            "<p style='color:#34d399;font-size:22px;margin:0;'>⚡ Электричество</p>"
            "<p style='color:#f8fafc;font-size:28px;font-weight:700;margin:8px 0 4px;'>±3%</p>"
            "<p style='color:#94a3b8;font-size:13px;margin:0;'>Стабильно (норматив в норме)</p>"
            "</div>",
            unsafe_allow_html=True,
        )
