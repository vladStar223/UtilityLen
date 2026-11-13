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


def render_sidebar(cases: list, client=None) -> dict:
    """Render the folder-style navigation sidebar with theme toggle and calculation history."""
    if client is None:
        try:
            from api_client import get_api_client

            client = get_api_client()
        except Exception:
            client = None

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
        f"<div style='padding: 0.2rem 0 0.4rem 0;'>"
        f"<h2 style='margin:0; font-size: 20px; font-weight: 800; color: {title_color}; letter-spacing: -0.01em;'>UtilityLens</h2>"
        f"</div>",
        unsafe_allow_html=True,
    )
    
    if st.sidebar.button("👤 Мой профиль и статистика", key="btn_go_profile", use_container_width=True):
        st.session_state["active_screen"] = "profile"
        st.rerun()

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

    # User's calculations history
    with st.sidebar.expander("📜 Моя история расчётов", expanded=True):
        history = []
        if client is not None:
            try:
                history = client.get_comparisons_history()
            except Exception:
                history = []

        if history:
            for idx, item in enumerate(history):
                c_id = item.get("comparison_id", "")
                delta = float(item.get("delta_abs", 0.0))
                summary = item.get("summary", {}) or {}
                period = summary.get("curr_period") or item.get("created_at", "")[:10]
                status = item.get("status_level", "ok")
                icon = "🔴" if status == "red" else ("🟡" if status == "yellow" else "🟢")
                btn_label = f"{icon} {period} ({delta:+,.2f} ₽)"
                if st.button(btn_label, key=f"hist_{c_id}_{idx}", use_container_width=True):
                    with st.spinner("Загрузка отчёта..."):
                        report = client.get_comparison(c_id)
                    if report and not report.get("error"):
                        st.session_state["analysis_result"] = report
                        st.session_state["comparison_id"] = c_id
                        st.session_state["active_screen"] = "analysis"
                        st.rerun()
                    elif report and report.get("error"):
                        st.error(report["error"])
        else:
            st.caption("Нет сохранённых расчётов")

    st.sidebar.markdown(
        f"<p style='margin: 12px 0 8px 2px; font-size: 11px; font-weight: 700; color: {sub_color}; text-transform: uppercase; letter-spacing: 0.05em;'>📁 Каталог квитанций по типам услуг</p>",
        unsafe_allow_html=True,
    )

    def _open_case(case_id: str) -> None:
        st.session_state["case_id"] = case_id
        st.session_state["analysis_result"] = None
        st.session_state["active_screen"] = "analysis"
        st.rerun()

    # Category Folders with clean styling
    with st.sidebar.expander("💧 Водоснабжение и водоотведение"):
        if st.button("ХВС и ГВС, перерасчеты", key="btn_folder_water", use_container_width=True):
            _open_case("case_02_coeff_15")

    with st.sidebar.expander("🔥 Теплоснабжение"):
        if st.button("Отопление (по Гкал)", key="btn_folder_heat", use_container_width=True):
            _open_case("case_01_heating_spike")

    with st.sidebar.expander("⚡ Электроснабжение"):
        if st.button("День/Ночь, соцнорма", key="btn_folder_elec", use_container_width=True):
            _open_case("case_elec_default")

    with st.sidebar.expander("📑 Единый платежный документ (ЕПД)"):
        if st.button("Комплексная квитанция", key="btn_folder_epd", use_container_width=True):
            _open_case("case_epd_default")

    with st.sidebar.expander("🏢 Капитальный ремонт и содержание"):
        if st.button("Общедомовые нужды", key="btn_folder_cap", use_container_width=True):
            _open_case("case_cap_default")

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
