"""Anomalies and overpayment warnings component."""
import streamlit as st


def render_anomalies(anomalies: list):
    """Render the list of detected anomalies with severity badges."""
    st.subheader("🚨 Предупреждения и скрытые переплаты")

    if not anomalies:
        st.info("✅ Аномалий и скрытых штрафов не обнаружено.")
        return

    for a in anomalies:
        sev = a.get("severity", "yellow")
        is_red = sev == "red"
        icon = "🔴" if is_red else "🟡"
        impact = a.get("impact_rub", 0)
        title = a.get("title", "Аномалия")
        hint = a.get("hint", "")

        bg_color = "#fff1f2" if is_red else "#fefce8"
        border_color = "#fecdd3" if is_red else "#fde047"
        text_badge_color = "#be123c" if is_red else "#854d0e"

        card_html = f"""
<div style="
    background: {bg_color};
    border: 1.5px solid {border_color};
    border-radius: 18px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.02);
">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;">
        <div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 18px;">{icon}</span>
                <span style="font-size: 16px; font-weight: 700; color: {text_badge_color};">
                    {title}
                </span>
            </div>
            <p style="margin: 6px 0 0 0; font-size: 13px; color: #475569; line-height: 1.5;">
                <strong>Причина:</strong> {hint}
            </p>
        </div>
        <div style="text-align: right; min-width: 130px;">
            <span style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase;">
                Переплата
            </span>
            <div style="font-size: 20px; font-weight: 800; color: {text_badge_color};">
                +{impact:,.2f} ₽
            </div>
        </div>
    </div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
