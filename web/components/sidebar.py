"""Sidebar component."""
import streamlit as st


def render_sidebar(cases: list) -> dict:
    """Render the folder-style navigation sidebar and mutate session state."""
    if "theme_dark" not in st.session_state:
        st.session_state["theme_dark"] = True
    if "active_screen" not in st.session_state:
        st.session_state["active_screen"] = "analysis"

    st.sidebar.title("🏠 UtilityLens")
    st.sidebar.caption("Интеллектуальный аудит квитанций ЖКХ")

    top1, top2 = st.sidebar.columns([4, 1])
    with top1:
        if st.button("🏠 Главная", use_container_width=True):
            st.session_state["active_screen"] = "upload"
            st.rerun()
    with top2:
        theme_icon = "☀️" if st.session_state["theme_dark"] else "🌙"
        if st.button(theme_icon, use_container_width=True):
            st.session_state["theme_dark"] = not st.session_state["theme_dark"]
            st.rerun()

    st.sidebar.markdown("---")

    def _open_case(case_id: str) -> None:
        st.session_state["case_id"] = case_id
        st.session_state["analysis_result"] = None
        st.session_state["active_screen"] = "analysis"
        st.rerun()

    with st.sidebar.expander("💧 Холодная вода (ХВС)", expanded=False):
        if st.button("🔴 Коэфф. 1.5 (+245 ₽)", use_container_width=True):
            _open_case("case_02_coeff_15")

    with st.sidebar.expander("🔥 Отопление (Гкал)", expanded=False):
        if st.button("🟡 Морозы (+1 700 ₽)", use_container_width=True):
            _open_case("case_01_heating_spike")

    with st.sidebar.expander("⚡ Электричество", expanded=False):
        st.sidebar.info("Двухтарифный Т1/Т2")

    with st.sidebar.expander("♨️ Горячая вода (ГВС)", expanded=False):
        if st.button("🔵 Индексация +9%", use_container_width=True):
            _open_case("case_03_tariff_index")

    st.sidebar.markdown("---")

    if st.sidebar.button("📈 График изменения цен", use_container_width=True):
        st.session_state["active_screen"] = "trends"
        st.rerun()

    if st.sidebar.button("⚖️ Чат с AI-Юристом", use_container_width=True):
        st.session_state["active_screen"] = "chat"
        st.rerun()

    return {
        "active_screen": st.session_state["active_screen"],
        "theme_dark": st.session_state["theme_dark"],
        "case_id": st.session_state.get("case_id"),
    }
