"""Streamlit root application."""
import streamlit as st
from api_client import ApiClient

st.set_page_config(page_title="UtilityLens", layout="wide")
st.title("UtilityLens")

client = ApiClient()

try:
    comparison = client.compare_bills()
    summary = comparison.get("summary", {})

    prev_total = summary.get("prev_total", 0.0)
    curr_total = summary.get("curr_total", 0.0)
    delta_abs = summary.get("delta_abs", 0.0)

    col_prev, col_curr, col_delta = st.columns(3)
    col_prev.metric("Было", f"{prev_total:,.2f} ₽")
    col_curr.metric("Стало", f"{curr_total:,.2f} ₽")
    col_delta.metric("Дельта", f"{delta_abs:+,.2f} ₽")

    st.success("API Client инициализирован успешно!")
except Exception as e:
    st.error(f"Ошибка при инициализации API Client: {e}")
