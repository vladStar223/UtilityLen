"""Sidebar component with category folders and theme toggle."""
import streamlit as st


def render_sidebar(cases: list) -> dict:
    """Render the folder-style navigation sidebar and mutate session state."""
    if "theme_dark" not in st.session_state:
        st.session_state["theme_dark"] = True
    if "active_screen" not in st.session_state:
        st.session_state["active_screen"] = "analysis"
    if "case_id" not in st.session_state:
        st.session_state["case_id"] = "case_02_coeff_15"

    st.sidebar.title("🏠 UtilityLens")
    st.sidebar.caption("Интеллектуальный аудит квитанций ЖКХ")

    # Prominent Header Buttons: Theme Switcher & Home
    col_theme, col_home = st.sidebar.columns([1, 1])
    with col_theme:
        theme_icon = "🌙 Тёмная" if st.session_state["theme_dark"] else "☀️ Светлая"
        if st.button(theme_icon, key="btn_theme_toggle", use_container_width=True):
            st.session_state["theme_dark"] = not st.session_state["theme_dark"]
            st.rerun()
    with col_home:
        if st.button("🏠 Главная", key="btn_go_home", use_container_width=True):
            st.session_state["active_screen"] = "upload"
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 📁 Папки услуг")

    def _open_case(case_id: str) -> None:
        st.session_state["case_id"] = case_id
        st.session_state["analysis_result"] = None
        st.session_state["active_screen"] = "analysis"
        st.rerun()

    # Category Folders (expanded=True so user sees items immediately)
    with st.sidebar.expander("💧 Холодная вода (ХВС)", expanded=True):
        if st.button("🔴 Коэфф. 1.5 (+245.18 ₽)", key="btn_folder_water_spike", use_container_width=True):
            _open_case("case_02_coeff_15")
        st.caption("Окт 2026: базовый расчет (324 ₽)")

    with st.sidebar.expander("🔥 Отопление (Гкал)", expanded=True):
        if st.button("🟡 Морозы (+1 700 ₽)", key="btn_folder_heat_spike", use_container_width=True):
            _open_case("case_01_heating_spike")
        st.caption("Ноя 2026: скачок потребления")

    with st.sidebar.expander("♨️ Горячая вода (ГВС)", expanded=True):
        if st.button("🔵 Индексация +9%", key="btn_folder_hot_index", use_container_width=True):
            _open_case("case_03_tariff_index")
        st.caption("Июль 2026: плановое повышение")

    with st.sidebar.expander("⚡ Электричество", expanded=False):
        st.caption("Двухтарифный Т1/Т2: 1 240 ₽")

    st.sidebar.markdown("---")

    # Bottom Primary Action Buttons
    if st.sidebar.button("📈 График изменения цен", key="btn_open_trends", use_container_width=True):
        st.session_state["active_screen"] = "trends"
        st.rerun()

    if st.sidebar.button("⚖️ Чат с AI-Юристом", key="btn_open_chat", use_container_width=True, type="primary"):
        st.session_state["active_screen"] = "chat"
        st.rerun()

    return {
        "active_screen": st.session_state["active_screen"],
        "theme_dark": st.session_state["theme_dark"],
        "case_id": st.session_state.get("case_id"),
    }
