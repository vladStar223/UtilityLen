"""Global pastel glassmorphism styling for the Streamlit app."""
import streamlit as st


def apply_styles(is_dark: bool) -> None:
    """Inject custom CSS and adapt the palette to the current theme."""
    if is_dark:
        app_bg = "radial-gradient(circle at 15% 15%, #2e2640 0%, #171520 50%, #0d0c14 100%)"
        text_color = "#f1f5f9"
        glass_bg = "rgba(255, 255, 255, 0.06)"
        glass_border = "rgba(255, 255, 255, 0.14)"
        glass_shadow = "0 15px 35px rgba(0,0,0,0.4)"
        accent = "#c4b5fd"
        accent_strong = "#a78bfa"
        button_bg = "rgba(196, 181, 253, 0.12)"
        button_border = "rgba(196, 181, 253, 0.35)"
        button_text = "#ede9fe"
        sidebar_bg = "rgba(23, 21, 32, 0.85)"
    else:
        app_bg = "radial-gradient(circle at 10% 10%, #ede9fe 0%, #f1f5f9 50%, #e2e8f0 100%)"
        text_color = "#1e293b"
        glass_bg = "rgba(255, 255, 255, 0.78)"
        glass_border = "rgba(255, 255, 255, 0.95)"
        glass_shadow = "0 15px 35px rgba(100,116,139,0.14)"
        accent = "#8b5cf6"
        accent_strong = "#7c3aed"
        button_bg = "rgba(139, 92, 246, 0.12)"
        button_border = "rgba(139, 92, 246, 0.35)"
        button_text = "#4c1d95"
        sidebar_bg = "rgba(248, 250, 252, 0.88)"

    css = """
<style>
/* Keep header transparent but preserve sidebar collapse/expand controls */
header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stToolbar"] {
    display: none !important;
}
#MainMenu, footer {
    visibility: hidden;
}

/* Ensure sidebar toggle button is always visible and styled */
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: __GLASS_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 12px !important;
    color: __TEXT_COLOR__ !important;
    box-shadow: __GLASS_SHADOW__ !important;
    margin: 8px !important;
    z-index: 100000 !important;
}

.stApp {
    background: __APP_BG__;
    color: __TEXT_COLOR__;
}

/* Glass cards: bordered containers, metrics and generic containers */
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
    padding: 1.25rem 1.5rem;
}

[data-testid="stMetric"] {
    padding: 1rem 1.25rem;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: __SIDEBAR_BG__ !important;
    backdrop-filter: blur(28px) !important;
    -webkit-backdrop-filter: blur(28px) !important;
    border-right: 1px solid __GLASS_BORDER__ !important;
}
[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
    gap: 0.6rem !important;
}

/* Expanders in sidebar */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: __GLASS_BG__ !important;
    border: 1px solid __GLASS_BORDER__ !important;
    border-radius: 16px !important;
    margin-bottom: 0.4rem !important;
}

/* Buttons */
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

/* Primary button accent */
.stButton > button[kind="primary"] {
    background: __ACCENT_STRONG__ !important;
    border-color: __ACCENT__ !important;
    color: #ffffff !important;
}
</style>
"""
    css = (
        css.replace("__APP_BG__", app_bg)
        .replace("__TEXT_COLOR__", text_color)
        .replace("__GLASS_BG__", glass_bg)
        .replace("__SIDEBAR_BG__", sidebar_bg)
        .replace("__GLASS_BORDER__", glass_border)
        .replace("__GLASS_SHADOW__", glass_shadow)
        .replace("__ACCENT__", accent)
        .replace("__ACCENT_STRONG__", accent_strong)
        .replace("__BUTTON_BG__", button_bg)
        .replace("__BUTTON_BORDER__", button_border)
        .replace("__BUTTON_TEXT__", button_text)
    )

    st.markdown(css, unsafe_allow_html=True)
