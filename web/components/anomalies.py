"""Anomalies and overpayment warnings component supporting both themes."""
import streamlit as st


def render_anomalies(anomalies: list):
    """Render the list of detected anomalies with adaptive theme styling."""
    st.subheader("🚨 Предупреждения и скрытые переплаты")

    if not anomalies:
        st.info("✅ Аномалий и скрытых штрафов не обнаружено.")
        return

    is_dark = st.session_state.get("theme_dark", False)

    for a in anomalies:
        sev = a.get("severity", "yellow")
        is_red = sev == "red"
        icon = "🔴" if is_red else "🟡"
        impact = a.get("impact_rub", 0)
        title = a.get("title", "Аномалия")
        hint = a.get("hint", "")

        if is_dark:
            bg_color = "rgba(225, 29, 72, 0.15)" if is_red else "rgba(234, 179, 8, 0.15)"
            border_color = "rgba(244, 63, 94, 0.35)" if is_red else "rgba(234, 179, 8, 0.35)"
            text_badge_color = "#fda4af" if is_red else "#fde047"
            hint_color = "#cbd5e1"
            impact_color = "#fb7185" if is_red else "#fde047"
        else:
            bg_color = "#fff1f2" if is_red else "#fefce8"
            border_color = "#fecdd3" if is_red else "#fde047"
            text_badge_color = "#be123c" if is_red else "#854d0e"
            hint_color = "#475569"
            impact_color = "#be123c" if is_red else "#854d0e"

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
            <p style="margin: 6px 0 0 0; font-size: 13px; color: {hint_color}; line-height: 1.5;">
                <strong>Причина:</strong> {hint}
            </p>
        </div>
        <div style="text-align: right; min-width: 130px;">
            <span style="font-size: 11px; font-weight: 600; opacity: 0.7; text-transform: uppercase;">
                Переплата
            </span>
            <div style="font-size: 20px; font-weight: 800; color: {impact_color};">
                +{impact:,.2f} ₽
            </div>
        </div>
    </div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)
