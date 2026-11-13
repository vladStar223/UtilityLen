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
        icon = "🔴" if sev == "red" else "🟡"
        impact = a.get("impact_rub", 0)

        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"### {icon} {a.get('title', 'Аномалия')}")
            c1.markdown(f"**Причина:** {a.get('hint', '')}")
            c2.metric("Переплата", f"{impact:+,.2f} ₽")
