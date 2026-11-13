"""AI plain-language explanation component supporting both themes."""
import streamlit as st


def render_ai_explanation(ai_summary: str, items: list = None) -> None:
    """Render a prominent neural-network summary card explaining the bill in plain language."""
    if not ai_summary:
        return

    is_dark = st.session_state.get("theme_dark", False)
    bg_gradient = "linear-gradient(135deg, rgba(76, 29, 149, 0.25) 0%, rgba(30, 27, 75, 0.4) 100%)" if is_dark else "linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%)"
    border_color = "rgba(167, 139, 250, 0.4)" if is_dark else "#c4b5fd"
    text_color = "#ede9fe" if is_dark else "#1e1b4b"
    title_color = "#c4b5fd" if is_dark else "#6d28d9"
    badge_bg = "rgba(167, 139, 250, 0.2)" if is_dark else "rgba(109, 40, 217, 0.12)"
    badge_text = "#ddd6fe" if is_dark else "#5b21b6"

    st.markdown("### 🧠 Заключение AI-аналитика («Переводчик на человеческий»)")

    card_html = f"""
<div style="
    background: {bg_gradient};
    border: 1.5px solid {border_color};
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08);
    margin-bottom: 1.2rem;
">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 22px;">🤖</span>
            <span style="font-size: 14px; font-weight: 700; color: {title_color}; text-transform: uppercase; letter-spacing: 0.04em;">
                Интеллектуальная расшифровка
            </span>
        </div>
        <span style="
            background: {badge_bg};
            color: {badge_text};
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
            border: 1px solid {border_color};
        ">
            ПП РФ № 354 • Факторный разбор
        </span>
    </div>
    <p style="
        margin: 0;
        font-size: 15px;
        line-height: 1.65;
        color: {text_color};
        font-weight: 500;
    ">
        {ai_summary}
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
                    name = it.get("display_name", "Услуга")
                    expl = it.get("plain_explanation")
                    st.markdown(f"• **{name}:** {expl}")
