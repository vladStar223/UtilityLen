"""Streamlit root application."""
import streamlit as st

from api_client import get_api_client
from components.anomalies import render_anomalies
from components.kpi_cards import render_kpi_cards
from components.sidebar import render_sidebar

st.set_page_config(page_title="UtilityLens", layout="wide")

client = get_api_client()
cases = client.get_cases()
sidebar = render_sidebar(cases)

if sidebar["trigger"]:
    if sidebar["mode"] == "Демо-кейсы (1 клик)":
        result = client.compare_bills(sidebar["case_id"])
        render_kpi_cards(result.get("summary", {}), result.get("factor_breakdown", {}))
        render_anomalies(result.get("anomalies", []))
    else:
        if sidebar["file"] is not None:
            st.info("📄 Файл получен. В оффлайн-режиме выполняется эмуляция разбора локальным парсером.")
        else:
            st.warning("Пожалуйста, загрузите квитанцию перед анализом.")
