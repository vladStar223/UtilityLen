"""Global pastel glassmorphism styling for the Streamlit app."""
import streamlit as st


def apply_styles(is_dark: bool) -> None:
    """Inject custom CSS and adapt the palette to the current theme."""
    if is_dark:
        app_bg = "radial-gradient(circle at 15% 15%, #2e2640 0%, #171520 50%, #0d0c14 100%)"
        text_color = "#f8fafc"
        text_muted = "#94a3b8"
        glass_bg = "rgba(255, 255, 255, 0.06)"
        glass_border = "rgba(255, 255, 255, 0.14)"
        glass_shadow = "0 15px 35px rgba(0,0,0,0.4)"
        accent = "#c4b5fd"
        accent_strong = "#a78bfa"
        button_bg = "rgba(196, 181, 253, 0.12)"
        button_border = "rgba(196, 181, 253, 0.35)"
        button_text = "#ede9fe"
        sidebar_bg = "rgba(23, 21, 32, 0.95)"
        input_bg = "rgba(30, 27, 43, 0.85)"
        chat_user_bg = "rgba(139, 92, 246, 0.25)"
        chat_assistant_bg = "rgba(255, 255, 255, 0.06)"
    else:
        app_bg = "radial-gradient(circle at 10% 10%, #ede9fe 0%, #f8fafc 50%, #e2e8f0 100%)"
        text_color = "#0f172a"
        text_muted = "#475569"
        glass_bg = "rgba(255, 255, 255, 0.85)"
        glass_border = "rgba(203, 213, 225, 0.9)"
        glass_shadow = "0 15px 35px rgba(100,116,139,0.12)"
        accent = "#8b5cf6"
        accent_strong = "#7c3aed"
        button_bg = "rgba(139, 92, 246, 0.12)"
        button_border = "rgba(139, 92, 246, 0.35)"
        button_text = "#4c1d95"
        sidebar_bg = "rgba(255, 255, 255, 0.94)"
        input_bg = "rgba(255, 255, 255, 0.95)"
        chat_user_bg = "rgba(139, 92, 246, 0.15)"
        chat_assistant_bg = "rgba(255, 255, 255, 0.85)"

    css = """
<style>
/* 1. SIDEBAR FIXED LEFT & VISIBLE */
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
}

.stApp {
    background: __APP_BG__ !important;
    color: __TEXT_COLOR__ !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stToolbar"], #MainMenu, footer {
    display: none !important;
}

/* 2. UNIVERSAL HIGH CONTRAST TYPOGRAPHY */
h1, h2, h3, h4, h5, h6 {
    color: __TEXT_COLOR__ !important;
    font-weight: 700 !important;
}

p, span, label, li {
    color: __TEXT_COLOR__;
}

.stMarkdown, [data-testid="stMarkdownContainer"] {
    color: __TEXT_COLOR__ !important;
}

[data-testid="stMarkdownContainer"] p {
    color: __TEXT_COLOR__ !important;
}

/* Captions and muted text */
.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: __TEXT_MUTED__ !important;
}

/* 3. METRIC CARDS READABILITY */
[data-testid="stMetricValue"] {
    color: __TEXT_COLOR__ !important;
    font-weight: 800 !important;
}

[data-testid="stMetricValue"] * {
    color: __TEXT_COLOR__ !important;
}

[data-testid="stMetricLabel"] {
    color: __TEXT_MUTED__ !important;
    font-weight: 600 !important;
}

[data-testid="stMetricLabel"] * {
    color: __TEXT_MUTED__ !important;
}

/* 4. GLASS CARDS */
div[data-testid="stVerticalBlockBorderWrapper"],
.stMetric,
[data-testid="stMetric"] {
    background: __GLASS_BG__ !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 24px !important;
    box-shadow: __GLASS_SHADOW__ !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 1.25rem 1.5rem !important;
}

[data-testid="stMetric"] {
    padding: 1rem 1.25rem !important;
}

/* 5. SIDEBAR ELEMENTS */
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.65rem !important;
    padding-top: 1rem !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: __GLASS_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 16px !important;
    margin-bottom: 0.4rem !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: __TEXT_COLOR__ !important;
    font-weight: 600 !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary span {
    color: __TEXT_COLOR__ !important;
}

/* 6. BUTTONS */
.stButton > button {
    border-radius: 14px !important;
    border: 1px solid __BUTTON_BORDER__ !important;
    background: __BUTTON_BG__ !important;
    color: __BUTTON_TEXT__ !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.22s ease !important;
}

.stButton > button:hover {
    background: __ACCENT_STRONG__ !important;
    border-color: __ACCENT__ !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(139, 92, 246, 0.3) !important;
}

.stButton > button[kind="primary"] {
    background: __ACCENT_STRONG__ !important;
    border-color: __ACCENT__ !important;
    color: #ffffff !important;
}

/* 7. CHAT & INPUTS */
[data-testid="stChatMessage"] {
    background: __CHAT_ASSISTANT_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 18px !important;
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
}

[data-testid="stChatInput"] textarea {
    color: __TEXT_COLOR__ !important;
}

/* Multiselect in Light & Dark */
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
        .replace("__INPUT_BG__", input_bg)
        .replace("__CHAT_USER_BG__", chat_user_bg)
        .replace("__CHAT_ASSISTANT_BG__", chat_assistant_bg)
        .replace("__GLASS_BORDER__", glass_border)
        .replace("__GLASS_SHADOW__", glass_shadow)
        .replace("__ACCENT__", accent)
        .replace("__ACCENT_STRONG__", accent_strong)
        .replace("__BUTTON_BG__", button_bg)
        .replace("__BUTTON_BORDER__", button_border)
        .replace("__BUTTON_TEXT__", button_text)
    )

    st.markdown(css, unsafe_allow_html=True)
