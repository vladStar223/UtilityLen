"""Sidebar component with category folders — unified light theme."""
import streamlit as st


def render_sidebar(cases: list) -> dict:
    """Render the folder-style navigation sidebar in unified light theme."""
    if "active_screen" not in st.session_state:
        st.session_state["active_screen"] = "analysis"
    if "case_id" not in st.session_state:
        st.session_state["case_id"] = "case_02_coeff_15"

    st.sidebar.markdown(
        "<div style='padding: 0.2rem 0 0.8rem 0;'>"
        "<h2 style='margin:0; font-size: 22px; font-weight: 800; color: #0f172a; letter-spacing: -0.02em;'>🏠 UtilityLens</h2>"
        "<p style='margin: 4px 0 0 0; font-size: 12px; color: #64748b; font-weight: 500;'>Интеллектуальный аудит квитанций ЖКХ</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Primary Upload / Home Button
    if st.sidebar.button("📄 + Загрузить новую квитанцию", key="btn_go_home", use_container_width=True):
        st.session_state["active_screen"] = "upload"
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<p style='margin: 0 0 8px 2px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;'>📁 Папки услуг (История)</p>",
        unsafe_allow_html=True,
    )

    def _open_case(case_id: str) -> None:
        st.session_state["case_id"] = case_id
        st.session_state["analysis_result"] = None
        st.session_state["active_screen"] = "analysis"
        st.rerun()

    # Category Folders with clean styling
    with st.sidebar.expander("💧 Холодная вода (ХВС)", expanded=True):
        if st.button("🔴 Коэфф. 1.5 (+245.18 ₽)", key="btn_folder_water_spike", use_container_width=True):
            _open_case("case_02_coeff_15")
        st.caption("Окт 2026: базовый счет (324 ₽)")

    with st.sidebar.expander("🔥 Отопление (Гкал)", expanded=True):
        if st.button("🟡 Морозы (+1 700.00 ₽)", key="btn_folder_heat_spike", use_container_width=True):
            _open_case("case_01_heating_spike")
        st.caption("Ноя 2026: скачок потребления тепла")

    with st.sidebar.expander("♨️ Горячая вода (ГВС)", expanded=True):
        if st.button("🔵 Индексация (+450.00 ₽)", key="btn_folder_hot_index", use_container_width=True):
            _open_case("case_03_tariff_index")
        st.caption("Июль 2026: плановый рост тарифов +9%")

    with st.sidebar.expander("⚡ Электричество", expanded=False):
        st.caption("Двухтарифный учет Т1/Т2: 1 240 ₽")

    st.sidebar.markdown("---")

    # Bottom Navigation Buttons
    if st.sidebar.button("📈 График изменения цен", key="btn_open_trends", use_container_width=True):
        st.session_state["active_screen"] = "trends"
        st.rerun()

    if st.sidebar.button("⚖️ Чат с AI-Юристом", key="btn_open_chat", use_container_width=True, type="primary"):
        st.session_state["active_screen"] = "chat"
        st.rerun()

    return {
        "active_screen": st.session_state["active_screen"],
        "case_id": st.session_state.get("case_id"),
    }
