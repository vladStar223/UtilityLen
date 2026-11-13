"""Streamlit root application — adaptive theme with AI explanation card."""
import streamlit as st

from api_client import get_api_client
from components.ai_explanation import render_ai_explanation
from components.anomalies import render_anomalies
from components.chat import render_chat_view
from components.kpi_cards import render_kpi_cards
from components.sidebar import render_sidebar
from components.trends_view import render_trends_view
from components.upload_view import render_upload_view
from styles import apply_styles

st.set_page_config(
    page_title="UtilityLens — Аудит квитанций ЖКХ",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "theme_dark" not in st.session_state:
    st.session_state["theme_dark"] = False
if "active_screen" not in st.session_state:
    st.session_state["active_screen"] = "analysis"
if "case_id" not in st.session_state:
    st.session_state["case_id"] = "case_02_coeff_15"
if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None

# Apply adaptive styles based on selected theme
apply_styles(st.session_state["theme_dark"])

client = get_api_client()
cases = client.get_cases()
sidebar_state = render_sidebar(cases)

screen = st.session_state["active_screen"]

if screen == "upload":
    render_upload_view(client)
elif screen == "analysis":
    if st.session_state["analysis_result"] is None:
        st.session_state["analysis_result"] = client.compare_bills(
            st.session_state["case_id"]
        )
    result = st.session_state["analysis_result"]

    # 1. KPI Cards
    render_kpi_cards(result.get("summary", {}), result.get("factor_breakdown", {}))

    # 2. Prominent AI Neural Network Explanation
    render_ai_explanation(result.get("ai_summary", ""), result.get("items", []))

    # 3. Red Flag Anomalies
    render_anomalies(result.get("anomalies", []))

elif screen == "trends":
    render_trends_view()
elif screen == "chat":
    render_chat_view(client)
