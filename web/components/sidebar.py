"""Sidebar component."""
import streamlit as st


def render_sidebar(cases: list) -> dict:
    """Render the navigation sidebar and return its state."""
    st.sidebar.title("🏠 UtilityLens")
    st.sidebar.caption("Интеллектуальный аудит квитанций ЖКХ")

    mode = st.sidebar.radio(
        "Режим работы:",
        ["Демо-кейсы (1 клик)", "Загрузить квитанцию"],
        index=0,
    )

    selected_case_id = "case_02_coeff_15"
    uploaded_file = None

    if mode == "Демо-кейсы (1 клик)":
        case_titles = {c["case_id"]: f"{c['title']}" for c in cases}
        selected_case_id = st.sidebar.selectbox(
            "Выберите сценарий:",
            list(case_titles.keys()),
            format_func=lambda x: case_titles[x],
        )
        case_info = next((c for c in cases if c["case_id"] == selected_case_id), None)
        if case_info:
            st.sidebar.info(case_info.get("description", ""))
    else:
        uploaded_file = st.sidebar.file_uploader(
            "Загрузите квитанцию (JSON/PDF)", type=["json", "pdf"]
        )
        st.sidebar.caption(
            "⚠️ В оффлайн-режиме загруженный файл эмулирует разбор через локальный парсер."
        )

    trigger = st.sidebar.button(
        "🔍 Анализировать квитанцию", type="primary", use_container_width=True
    )

    return {
        "mode": mode,
        "case_id": selected_case_id,
        "file": uploaded_file,
        "trigger": trigger,
    }
