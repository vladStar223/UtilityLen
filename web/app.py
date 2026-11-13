"""Streamlit root application."""
import streamlit as st

from api_client import get_api_client
from components.anomalies import render_anomalies
from components.kpi_cards import render_kpi_cards
from components.sidebar import render_sidebar
from components.upload_view import render_upload_view
from styles import apply_styles

st.set_page_config(page_title="UtilityLens", layout="wide")

if "theme_dark" not in st.session_state:
    st.session_state["theme_dark"] = True
if "active_screen" not in st.session_state:
    st.session_state["active_screen"] = "analysis"
if "case_id" not in st.session_state:
    st.session_state["case_id"] = "case_02_coeff_15"
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

apply_styles(st.session_state["theme_dark"])

client = get_api_client()
cases = client.get_cases()
render_sidebar(cases)

screen = st.session_state["active_screen"]

if screen == "upload":
    render_upload_view(client)
elif screen == "analysis":
    if st.session_state["analysis_result"] is None:
        st.session_state["analysis_result"] = client.compare_bills(
            st.session_state["case_id"]
        )
    result = st.session_state["analysis_result"]
    render_kpi_cards(result.get("summary", {}), result.get("factor_breakdown", {}))
    render_anomalies(result.get("anomalies", []))
elif screen == "trends":
    st.info("📈 Модуль динамики цен подключается на следующем шаге...")
elif screen == "chat":
    st.info("⚖️ Полноэкранный модуль AI-юриста подключается на следующем шаге...")
