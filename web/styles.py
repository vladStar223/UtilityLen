"""Unified clean light pastel glassmorphism styling for the Streamlit app."""
import streamlit as st


def apply_styles(is_dark: bool = False, *args, **kwargs) -> None:
    """Inject unified clean light glassmorphism styles with high contrast."""
    css = """
<style>
/* 1. APP BACKGROUND & GENERAL TYPOGRAPHY */
.stApp {
    background: radial-gradient(circle at 10% 10%, #ede9fe 0%, #f8fafc 50%, #f1f5f9 100%) !important;
    color: #0f172a !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
}

header[data-testid="stHeader"] {
    background: transparent !important;
}

[data-testid="stToolbar"], #MainMenu, footer {
    display: none !important;
}

/* 2. SIDEBAR - FIXED & CRISP LIGHT GLASS */
[data-testid="stSidebar"] {
    display: block !important;
    transform: none !important;
    visibility: visible !important;
    min-width: 320px !important;
    max-width: 380px !important;
    background: rgba(255, 255, 255, 0.94) !important;
    backdrop-filter: blur(28px) !important;
    -webkit-backdrop-filter: blur(28px) !important;
    border-right: 1px solid #e2e8f0 !important;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04) !important;
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

/* 3. SIDEBAR EXPANDERS - PURE WHITE (NO BLACK BOXES) */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 700 !important;
    border-radius: 14px !important;
    padding: 0.6rem 0.8rem !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    color: #7c3aed !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] summary * {
    color: #0f172a !important;
}

[data-testid="stSidebar"] [data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: #ffffff !important;
    padding: 0.5rem 0.8rem 0.8rem 0.8rem !important;
}

/* 4. HIGH CONTRAST TYPOGRAPHY ACROSS ALL ELEMENTS */
h1, h2, h3, h4, h5, h6 {
    color: #0f172a !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

p, span, label, li {
    color: #0f172a !important;
}

.stMarkdown, [data-testid="stMarkdownContainer"] {
    color: #0f172a !important;
}

[data-testid="stMarkdownContainer"] p {
    color: #0f172a !important;
}

.stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-weight: 500 !important;
}

/* 5. METRIC CARDS - CRISP BLACK DIGITS */
div[data-testid="stMetric"],
.stMetric {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
    padding: 1.25rem 1.4rem !important;
}

[data-testid="stMetricLabel"] {
    color: #475569 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
}

[data-testid="stMetricLabel"] * {
    color: #475569 !important;
}

[data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 1.85rem !important;
    font-weight: 900 !important;
    letter-spacing: -0.03em !important;
}

[data-testid="stMetricValue"] * {
    color: #0f172a !important;
}

/* 6. GENERIC BORDERED CONTAINERS */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 20px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04) !important;
    padding: 1.25rem 1.5rem !important;
}

/* 7. GREEN QR VERIFICATION BANNER */
div[data-testid="stNotification"][data-test-color="success"],
div.stAlert:has(div[data-testid="stNotificationContentSuccess"]) {
    background: #ecfdf5 !important;
    border: 1px solid #a7f3d0 !important;
    color: #065f46 !important;
    border-radius: 16px !important;
}

div.stAlert * {
    color: inherit !important;
}

/* 8. BUTTONS */
.stButton > button {
    border-radius: 12px !important;
    border: 1px solid #e2e8f0 !important;
    background: #ffffff !important;
    color: #0f172a !important;
    font-weight: 600 !important;
    padding: 0.55rem 1rem !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    background: #7c3aed !important;
    border-color: #7c3aed !important;
    color: #ffffff !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(124, 58, 237, 0.25) !important;
}

.stButton > button[kind="primary"] {
    background: #7c3aed !important;
    border-color: #7c3aed !important;
    color: #ffffff !important;
}

/* 9. CHAT ELEMENTS */
[data-testid="stChatMessage"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 18px !important;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.03) !important;
    padding: 1rem !important;
    color: #0f172a !important;
    margin-bottom: 0.75rem !important;
}

[data-testid="stChatMessage"] p {
    color: #0f172a !important;
}

[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1px solid #cbd5e1 !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05) !important;
}

[data-testid="stChatInput"] textarea {
    color: #0f172a !important;
}

/* 10. MULTISELECT & INPUTS */
[data-testid="stMultiSelect"] span {
    color: #0f172a !important;
}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)
