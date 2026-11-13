"""Anomalies and overpayment warnings component supporting both themes."""
import html

import streamlit as st


def render_anomalies(anomalies: list):
    """Render the list of detected anomalies with adaptive theme styling."""
    st.subheader("🚨 Предупреждения и скрытые переплаты")

    if not anomalies:
        st.info("✅ Аномалий и скрытых штрафов не обнаружено.")
        return

    is_dark = st.session_state.get("theme_dark", False)

    for idx, a in enumerate(anomalies):
        sev = a.get("severity", "yellow")
        is_red = sev == "red"
        icon = "🔴" if is_red else "🟡"
        impact = a.get("impact_rub", 0)
        title = a.get("title", "Аномалия")
        hint = a.get("hint", "")

        safe_title = html.escape(str(title))
        safe_hint = html.escape(str(hint))
        safe_impact = f"{float(impact or 0):,.2f}"

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

        col_text, col_btn = st.columns([4, 1.2])

        with col_text:
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
                    {safe_title}
                </span>
            </div>
            <p style="margin: 6px 0 0 0; font-size: 13px; color: {hint_color}; line-height: 1.5;">
                <strong>Причина:</strong> {safe_hint}
            </p>
        </div>
        <div style="text-align: right; min-width: 130px;">
            <span style="font-size: 11px; font-weight: 600; color: {hint_color}; text-transform: uppercase;">
                Переплата
            </span>
            <div style="font-size: 20px; font-weight: 800; color: {impact_color};">
                +{safe_impact} ₽
            </div>
        </div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

        with col_btn:
            if st.button(
                "⚖️ Оспорить с юристом",
                key=f"dispute_btn_{idx}",
                use_container_width=True,
            ):
                st.session_state["active_screen"] = "chat"
                st.session_state["pending_prompt"] = (
                    f"Законно ли начисление: {a.get('title')} "
                    f"на сумму {a.get('impact_rub', 0):,.2f} ₽? "
                    f"Подготовь текст претензии в УК."
                )
                st.rerun()
