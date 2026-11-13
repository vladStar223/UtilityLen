"""AI plain-language explanation component."""
import streamlit as st


def render_ai_explanation(ai_summary: str, items: list = None) -> None:
    """Render a prominent neural-network summary card explaining the bill in plain language."""
    if not ai_summary:
        return

    st.markdown("### 🧠 Заключение AI-аналитика («Переводчик на человеческий»)")

    card_html = f"""
<div style="
    background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
    border: 1.5px solid #c4b5fd;
    border-radius: 20px;
    padding: 1.4rem 1.6rem;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.08);
    margin-bottom: 1.2rem;
">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 22px;">🤖</span>
            <span style="font-size: 14px; font-weight: 700; color: #6d28d9; text-transform: uppercase; letter-spacing: 0.04em;">
                Интеллектуальная расшифровка
            </span>
        </div>
        <span style="
            background: rgba(109, 40, 217, 0.12);
            color: #5b21b6;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 999px;
            border: 1px solid rgba(109, 40, 217, 0.2);
        ">
            ПП РФ № 354 • Факторный разбор
        </span>
    </div>
    <p style="
        margin: 0;
        font-size: 15px;
        line-height: 1.65;
        color: #1e1b4b;
        font-weight: 500;
    ">
        {ai_summary}
    </p>
</div>
"""
    st.markdown(card_html, unsafe_allow_html=True)

    # If items have individual plain explanations, show them as a mini bullet list
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
