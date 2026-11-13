"""Sidebar component with category folders and theme toggle."""
import html

import streamlit as st

from utils.masking import mask_address, mask_personal_account


def _sanitize_case(case: dict) -> dict:
    return {
        "case_id": case.get("case_id", ""),
        "title": html.escape(str(case.get("title", ""))),
        "description": html.escape(str(case.get("description", ""))),
        "address": mask_address(str(case.get("address", ""))),
        "account": mask_personal_account(
            str(case.get("personal_account", "") or case.get("account", ""))
        ),
    }


def _render_case_pii(safe_cases: dict, case_id: str) -> None:
    case = safe_cases.get(case_id)
    if not case:
        return
    details = " ".join(x for x in (case["address"], case["account"]) if x)
    if details:
        st.caption(f"📍 {details}")


def render_sidebar(cases: list) -> dict:
    """Render the folder-style navigation sidebar with theme toggle."""
    if "theme_dark" not in st.session_state:
        st.session_state["theme_dark"] = False
    if "active_screen" not in st.session_state:
        st.session_state["active_screen"] = "analysis"
    if "case_id" not in st.session_state:
        st.session_state["case_id"] = "case_02_coeff_15"

    is_dark = st.session_state.get("theme_dark", False)
    title_color = "#f8fafc" if is_dark else "#0f172a"
    sub_color = "#94a3b8" if is_dark else "#64748b"

    safe_cases = {
        c["case_id"]: c
        for c in (_sanitize_case(c) for c in cases)
        if c.get("case_id")
    }

    st.sidebar.markdown(
        f"<div style='padding: 0.2rem 0 0.6rem 0;'>"
        f"<h2 style='margin:0; font-size: 24px; font-weight: 800; color: {title_color}; letter-spacing: -0.02em;'>🏠 UtilityLens</h2>"
        f"<p style='margin: 4px 0 0 0; font-size: 12px; font-weight: 500; color: {sub_color};'>Интеллектуальный аудит квитанций ЖКХ</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Top Action Buttons: Theme Toggle & New Bill
    col_theme, col_home = st.sidebar.columns([1, 1])
    with col_theme:
        theme_label = "🌙 Тёмная" if is_dark else "☀️ Светлая"
        if st.button(theme_label, key="btn_theme_toggle", use_container_width=True):
            st.session_state["theme_dark"] = not st.session_state["theme_dark"]
            st.rerun()

    with col_home:
        if st.button("📄 + Загрузить", key="btn_go_home", use_container_width=True):
            st.session_state["active_screen"] = "upload"
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<p style='margin: 0 0 8px 2px; font-size: 11px; font-weight: 700; color: {sub_color}; text-transform: uppercase; letter-spacing: 0.05em;'>📁 Папки услуг (История)</p>",
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
        _render_case_pii(safe_cases, "case_02_coeff_15")

    with st.sidebar.expander("🔥 Отопление (Гкал)", expanded=True):
        if st.button("🟡 Морозы (+1 700.00 ₽)", key="btn_folder_heat_spike", use_container_width=True):
            _open_case("case_01_heating_spike")
        st.caption("Ноя 2026: скачок потребления тепла")
        _render_case_pii(safe_cases, "case_01_heating_spike")

    with st.sidebar.expander("♨️ Горячая вода (ГВС)", expanded=True):
        if st.button("🔵 Индексация (+450.00 ₽)", key="btn_folder_hot_index", use_container_width=True):
            _open_case("case_03_tariff_index")
        st.caption("Июль 2026: плановый рост тарифов +9%")
        _render_case_pii(safe_cases, "case_03_tariff_index")

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
        "theme_dark": st.session_state["theme_dark"],
        "case_id": st.session_state.get("case_id"),
    }
