"""Global pastel glassmorphism styling for the Streamlit app."""
import streamlit as st


def apply_styles(is_dark: bool) -> None:
    """Inject custom CSS and adapt the palette to the current theme."""
    if is_dark:
        app_bg = "radial-gradient(circle at 15% 15%, #2e2640 0%, #171520 50%, #0d0c14 100%)"
        text_color = "#f1f5f9"
        glass_bg = "rgba(255, 255, 255, 0.05)"
        glass_border = "rgba(255, 255, 255, 0.12)"
        glass_shadow = "0 15px 35px rgba(0,0,0,0.4)"
        accent = "#c4b5fd"
        accent_strong = "#a78bfa"
        button_bg = "rgba(196, 181, 253, 0.12)"
        button_border = "rgba(196, 181, 253, 0.35)"
        button_text = "#ede9fe"
    else:
        app_bg = "radial-gradient(circle at 10% 10%, #ede9fe 0%, #f1f5f9 50%, #e2e8f0 100%)"
        text_color = "#1e293b"
        glass_bg = "rgba(255, 255, 255, 0.75)"
        glass_border = "rgba(255, 255, 255, 0.9)"
        glass_shadow = "0 15px 35px rgba(100,116,139,0.12)"
        accent = "#8b5cf6"
        accent_strong = "#7c3aed"
        button_bg = "rgba(139, 92, 246, 0.10)"
        button_border = "rgba(139, 92, 246, 0.30)"
        button_text = "#4c1d95"

    css = """
<style>
__HEADER_HIDDEN__
.stApp {
    background: __APP_BG__;
    color: __TEXT_COLOR__;
}

/* Glass cards: bordered containers, metrics and generic containers */
div[data-testid="stVerticalBlockBorderWrapper"],
.stMetric,
[data-testid="stMetric"] {
    background: __GLASS_BG__;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid __GLASS_BORDER__;
    border-radius: 24px;
    box-shadow: __GLASS_SHADOW__;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 1.25rem 1.5rem;
}

[data-testid="stMetric"] {
    padding: 1rem 1.25rem;
}

/* Sidebar glass panel */
[data-testid="stSidebar"] {
    background: __GLASS_BG__;
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-right: 1px solid __GLASS_BORDER__;
}

/* Buttons */
.stButton > button {
    border-radius: 16px;
    border: 1px solid __BUTTON_BORDER__;
    background: __BUTTON_BG__;
    color: __BUTTON_TEXT__;
    font-weight: 600;
    padding: 0.55rem 1.1rem;
    transition: all 0.25s ease;
    box-shadow: none;
}
.stButton > button:hover {
    background: __ACCENT_STRONG__;
    border-color: __ACCENT__;
    color: __TEXT_COLOR__;
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(139, 92, 246, 0.25);
}
.stButton > button:active {
    transform: translateY(0);
    box-shadow: none;
}

/* Primary button accent */
.stButton > button[kind="primary"] {
    background: __ACCENT_STRONG__;
    border-color: __ACCENT__;
    color: #ffffff;
}
</style>
"""
    css = (
        css.replace("__HEADER_HIDDEN__", "header { visibility: hidden; }")
        .replace("__APP_BG__", app_bg)
        .replace("__TEXT_COLOR__", text_color)
        .replace("__GLASS_BG__", glass_bg)
        .replace("__GLASS_BORDER__", glass_border)
        .replace("__GLASS_SHADOW__", glass_shadow)
        .replace("__ACCENT__", accent)
        .replace("__ACCENT_STRONG__", accent_strong)
        .replace("__BUTTON_BG__", button_bg)
        .replace("__BUTTON_BORDER__", button_border)
        .replace("__BUTTON_TEXT__", button_text)
    )

    st.markdown(css, unsafe_allow_html=True)
