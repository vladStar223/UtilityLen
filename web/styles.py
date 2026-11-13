"""Adaptive pastel glassmorphism styling supporting both Light and Dark themes."""
import streamlit as st


def apply_styles(is_dark: bool = False, *args, **kwargs) -> None:
    """Inject glassmorphism styles with high contrast and pixel-perfect theme support."""
    if is_dark:
        app_bg = "#0f172a"
        text_color = "#f8fafc"
        text_muted = "#94a3b8"
        glass_bg = "#1e293b"
        glass_border = "#334155"
        glass_shadow = "0 4px 16px rgba(0, 0, 0, 0.3)"
        sidebar_bg = "#0b1120"
        expander_bg = "#1e293b"
        button_bg = "#1e293b"
        button_border = "#334155"
        button_text = "#f8fafc"
        accent_strong = "#2563eb"
        accent = "#3b82f6"
        input_bg = "#1e293b"
        chat_bg = "#1e293b"
        alert_qr_bg = "#064e3b"
        alert_qr_border = "#059669"
        alert_qr_text = "#6ee7b7"
        delta_pill_bg = "rgba(239, 68, 68, 0.15)"
        delta_pill_border = "rgba(239, 68, 68, 0.3)"
        delta_pill_text = "#f87171"
    else:
        app_bg = "#f8fafc"
        text_color = "#0f172a"
        text_muted = "#64748b"
        glass_bg = "#ffffff"
        glass_border = "#e2e8f0"
        glass_shadow = "0 2px 10px rgba(0, 0, 0, 0.04)"
        sidebar_bg = "#ffffff"
        expander_bg = "#ffffff"
        button_bg = "#ffffff"
        button_border = "#e2e8f0"
        button_text = "#0f172a"
        accent_strong = "#1d4ed8"
        accent = "#2563eb"
        input_bg = "#ffffff"
        chat_bg = "#ffffff"
        alert_qr_bg = "#f0fdf4"
        alert_qr_border = "#86efac"
        alert_qr_text = "#166534"
        delta_pill_bg = "#fef2f2"
        delta_pill_border = "#fecaca"
        delta_pill_text = "#b91c1c"

    css = """
<style>
/* 1. APP BACKGROUND & GENERAL TYPOGRAPHY */
.stApp {
    background: __APP_BG__ !important;
    color: __TEXT_COLOR__ !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
}

[data-testid="stSidebarContent"],
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0.5rem !important;
}

.main .block-container {
    padding-top: 1rem !important;
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
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2) !important;
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
    tokens = {
        "__APP_BG__": app_bg,
        "__TEXT_COLOR__": text_color,
        "__TEXT_MUTED__": text_muted,
        "__GLASS_BG__": glass_bg,
        "__SIDEBAR_BG__": sidebar_bg,
        "__EXPANDER_BG__": expander_bg,
        "__INPUT_BG__": input_bg,
        "__CHAT_BG__": chat_bg,
        "__GLASS_BORDER__": glass_border,
        "__GLASS_SHADOW__": glass_shadow,
        "__ACCENT__": accent,
        "__ACCENT_STRONG__": accent_strong,
        "__BUTTON_BG__": button_bg,
        "__BUTTON_BORDER__": button_border,
        "__BUTTON_TEXT__": button_text,
        "__ALERT_QR_BG__": alert_qr_bg,
        "__ALERT_QR_BORDER__": alert_qr_border,
        "__ALERT_QR_TEXT__": alert_qr_text,
        "__DELTA_PILL_BG__": delta_pill_bg,
        "__DELTA_PILL_BORDER__": delta_pill_border,
        "__DELTA_PILL_TEXT__": delta_pill_text,
    }
    for placeholder, val in tokens.items():
        css = css.replace(placeholder, val)

    st.markdown(css, unsafe_allow_html=True)
