"""Adaptive pastel glassmorphism styling supporting both Light and Dark themes."""
import streamlit as st


def apply_styles(is_dark: bool = False, *args, **kwargs) -> None:
    """Inject glassmorphism styles with high contrast and pixel-perfect theme support."""
    if is_dark:
        app_bg = "radial-gradient(circle at 15% 15%, #2e2640 0%, #171520 50%, #0d0c14 100%)"
        text_color = "#f8fafc"
        text_muted = "#94a3b8"
        glass_bg = "rgba(255, 255, 255, 0.06)"
        glass_border = "rgba(255, 255, 255, 0.14)"
        glass_shadow = "0 15px 35px rgba(0,0,0,0.45)"
        sidebar_bg = "rgba(23, 21, 32, 0.96)"
        expander_bg = "rgba(255, 255, 255, 0.04)"
        button_bg = "rgba(196, 181, 253, 0.12)"
        button_border = "rgba(196, 181, 253, 0.35)"
        button_text = "#ede9fe"
        accent_strong = "#7c3aed"
        accent = "#a78bfa"
        input_bg = "rgba(30, 27, 43, 0.9)"
        chat_bg = "rgba(255, 255, 255, 0.06)"
        alert_qr_bg = "rgba(6, 78, 59, 0.45)"
        alert_qr_border = "rgba(16, 185, 129, 0.4)"
        alert_qr_text = "#6ee7b7"
        delta_pill_bg = "rgba(255, 255, 255, 0.08)"
        delta_pill_border = "rgba(255, 255, 255, 0.15)"
        delta_pill_text = "#fda4af"
    else:
        app_bg = "radial-gradient(circle at 10% 10%, #ede9fe 0%, #f8fafc 50%, #f1f5f9 100%)"
        text_color = "#0f172a"
        text_muted = "#475569"
        glass_bg = "#ffffff"
        glass_border = "#e2e8f0"
        glass_shadow = "0 4px 20px rgba(0, 0, 0, 0.04)"
        sidebar_bg = "rgba(255, 255, 255, 0.96)"
        expander_bg = "#ffffff"
        button_bg = "#ffffff"
        button_border = "#e2e8f0"
        button_text = "#0f172a"
        accent_strong = "#7c3aed"
        accent = "#8b5cf6"
        input_bg = "#ffffff"
        chat_bg = "#ffffff"
        alert_qr_bg = "#ecfdf5"
        alert_qr_border = "#a7f3d0"
        alert_qr_text = "#065f46"
        delta_pill_bg = "rgba(0, 0, 0, 0.04)"
        delta_pill_border = "rgba(0, 0, 0, 0.08)"
        delta_pill_text = "#be123c"

    css = """
<style>
/* 1. APP BACKGROUND & GENERAL TYPOGRAPHY */
.stApp {
    background: __APP_BG__ !important;
    color: __TEXT_COLOR__ !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"], #MainMenu, footer {
    display: none !important;
}

/* 2. SIDEBAR - FIXED & CRISP GLASS */
[data-testid="stSidebar"] {
    display: block !important;
    transform: none !important;
    visibility: visible !important;
    min-width: 320px !important;
    max-width: 380px !important;
    background: __SIDEBAR_BG__ !important;
    backdrop-filter: blur(28px) !important;
    -webkit-backdrop-filter: blur(28px) !important;
    border-right: 1px solid __GLASS_BORDER__ !important;
    box-shadow: __GLASS_SHADOW__ !important;
    z-index: 99 !important;
}

[data-testid="stSidebarCollapseButton"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

section.main {
    margin-left: 0 !important;
    padding-top: 1.5rem !important;
}

/* 3. SIDEBAR EXPANDERS */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: __EXPANDER_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background: transparent !important;
    color: __TEXT_COLOR__ !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    padding: 0.6rem 0.8rem !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary * {
    color: __TEXT_COLOR__ !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: transparent !important;
    padding: 0.5rem 0.8rem 0.8rem 0.8rem !important;
}

/* 4. HIGH CONTRAST TYPOGRAPHY */
h1, h2, h3, h4, h5, h6 {
    color: __TEXT_COLOR__ !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, li {
    color: __TEXT_COLOR__ !important;
}

.stMarkdown, [data-testid="stMarkdownContainer"] {
    color: __TEXT_COLOR__ !important;
}

[data-testid="stMarkdownContainer"] p {
    color: __TEXT_COLOR__ !important;
}

.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: __TEXT_MUTED__ !important;
    font-weight: 500 !important;
}

/* 5. METRIC CARDS */
div[data-testid="stMetric"],
.stMetric {
    background: __GLASS_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 20px !important;
    box-shadow: __GLASS_SHADOW__ !important;
    padding: 1.25rem 1.4rem !important;
}

[data-testid="stMetricLabel"] {
    color: __TEXT_MUTED__ !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

[data-testid="stMetricLabel"] * {
    color: __TEXT_MUTED__ !important;
}

[data-testid="stMetricValue"] {
    color: __TEXT_COLOR__ !important;
    font-size: 1.85rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em !important;
}

[data-testid="stMetricValue"] * {
    color: __TEXT_COLOR__ !important;
}

/* FIX: Metric Delta Pills — NO WHITE BOXES! */
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] > div {
    background: __DELTA_PILL_BG__ !important;
    border: 1px solid __DELTA_PILL_BORDER__ !important;
    border-radius: 999px !important;
    padding: 2px 10px !important;
    width: fit-content !important;
}

[data-testid="stMetricDelta"] * {
    color: __DELTA_PILL_TEXT__ !important;
}

/* 6. GENERIC BORDERED CONTAINERS */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: __GLASS_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 20px !important;
    box-shadow: __GLASS_SHADOW__ !important;
    padding: 1.25rem 1.5rem !important;
}

/* 7. FIX: GREEN QR VERIFICATION BANNER — NO SOLID WHITE BOX! */
div[data-testid="stAlert"],
div[data-testid="stNotification"],
div.stAlert {
    background: __ALERT_QR_BG__ !important;
    border: 1.5px solid __ALERT_QR_BORDER__ !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
}

div[data-testid="stAlert"] *,
div[data-testid="stNotification"] *,
div.stAlert * {
    color: __ALERT_QR_TEXT__ !important;
    background: transparent !important;
}

/* 8. BUTTONS */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid __BUTTON_BORDER__ !important;
    background: __BUTTON_BG__ !important;
    color: __BUTTON_TEXT__ !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: __ACCENT_STRONG__ !important;
    border-color: __ACCENT_STRONG__ !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.25) !important;
}

.stButton > button[kind="primary"] {
    background: __ACCENT_STRONG__ !important;
    border-color: __ACCENT_STRONG__ !important;
    color: #ffffff !important;
}

/* 9. CHAT ELEMENTS */
[data-testid="stChatMessage"] {
    background: __CHAT_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 18px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
    padding: 1rem !important;
    color: __TEXT_COLOR__ !important;
    margin-bottom: 0.75rem !important;
}

[data-testid="stChatMessage"] p {
    color: __TEXT_COLOR__ !important;
}

[data-testid="stChatInput"] {
    background: __INPUT_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
}

[data-testid="stChatInput"] textarea {
    color: __TEXT_COLOR__ !important;
}

/* 10. MULTISELECT & INPUTS */
[data-testid="stMultiSelect"] span {
    color: __TEXT_COLOR__ !important;
}
</style>
"""
    css = (
        css.replace("__APP_BG__", app_bg)
        .replace("__TEXT_COLOR__", text_color)
        .replace("__TEXT_MUTED__", text_muted)
        .replace("__GLASS_BG__", glass_bg)
        .replace("__SIDEBAR_BG__", sidebar_bg)
        .replace("__EXPANDER_BG__", expander_bg)
        .replace("__INPUT_BG__", input_bg)
        .replace("__CHAT_BG__", chat_bg)
        .replace("__GLASS_BORDER__", glass_border)
        .replace("__GLASS_SHADOW__", glass_shadow)
        .replace("__ACCENT__", accent)
        .replace("__ACCENT_STRONG__", accent_strong)
        .replace("__BUTTON_BG__", button_bg)
        .replace("__BUTTON_BORDER__", button_border)
        .replace("__BUTTON_TEXT__", button_text)
        .replace("__ALERT_QR_BG__", alert_qr_bg)
        .replace("__ALERT_QR_BORDER__", alert_qr_border)
        .replace("__ALERT_QR_TEXT__", alert_qr_text)
        .replace("__DELTA_PILL_BG__", delta_pill_bg)
        .replace("__DELTA_PILL_BORDER__", delta_pill_border)
        .replace("__DELTA_PILL_TEXT__", delta_pill_text)
    )

    st.markdown(css, unsafe_allow_html=True)
