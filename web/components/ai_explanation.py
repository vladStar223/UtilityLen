"""Expert calculation audit summary component supporting both themes."""
import html

import streamlit as st


def render_ai_explanation(ai_summary: str, items: list = None) -> None:
    """Render an expert audit summary card explaining the calculation in plain fintech style."""
    if not ai_summary:
        return

    is_dark = st.session_state.get("theme_dark", False)
    bg_color = "#1e293b" if is_dark else "#ffffff"
    border_color = "#334155" if is_dark else "#e2e8f0"
    text_color = "#f8fafc" if is_dark else "#0f172a"
    title_color = "#38bdf8" if is_dark else "#0369a1"
    badge_bg = "rgba(56, 189, 248, 0.12)" if is_dark else "#f0f9ff"
    badge_border = "rgba(56, 189, 248, 0.3)" if is_dark else "#bae6fd"
    badge_text = "#7dd3fc" if is_dark else "#0284c7"

    st.markdown("### 📑 Экспертное заключение аудита начислений")

    safe_summary = html.escape(str(ai_summary))

    card_html = f"""
<div style="
    background: {bg_color};
    border: 1px solid {border_color};
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
    margin-bottom: 1.2rem;
">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 14px; font-weight: 700; color: {title_color}; text-transform: uppercase; letter-spacing: 0.04em;">
                Результаты проверки
            </span>
        </div>
        <span style="
            background: {badge_bg};
            color: {badge_text};
            font-size: 12px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 6px;
            border: 1px solid {badge_border};
        ">
            Аудит по ПП РФ № 354 • Факторный разбор
        </span>
    </div>
    <p style="
        margin: 0;
        font-size: 14px;
        line-height: 1.6;
        color: {text_color};
        font-weight: 400;
    ">
        {safe_summary}
    </p>
</div>
"""
    st.markdown(card_html, unsafe_allow_html=True)

    if items:
        item_explanations = [
            it for it in items if it.get("plain_explanation")
        ]
        if item_explanations:
            with st.expander("📋 Построчные пояснения по каждой услуге", expanded=False):
                for it in item_explanations:
                    name = html.escape(str(it.get("display_name", "Услуга")))
                    expl = html.escape(str(it.get("plain_explanation", "")))
                    st.markdown(f"• **{name}:** {expl}")
