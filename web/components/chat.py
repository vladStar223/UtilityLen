"""Full-screen AI lawyer chat component."""
import streamlit as st

_WELCOME_MESSAGE = (
    "Здравствуйте! Я ваш юридический советник по ЖКХ. "
    "По вашей квитанции за Ноябрь 2026 обнаружен неправомерный повышающий "
    "коэффициент 1.5 по ХВС на сумму +245.18 ₽. Чем я могу помочь?"
)

_QUICK_PROMPTS = [
    "⚖️ Законно ли начисление 1.5?",
    "📄 Составить досудебную претензию в УК",
    "❓ Почему выросла общая сумма?",
]


def render_chat_view(client) -> None:
    """Render the full-screen AI lawyer chat screen."""

    # --- Header ---
    col_icon, col_title, col_status, col_back = st.columns([0.5, 3.5, 2, 1.5])
    with col_icon:
        st.markdown(
            "<div style='font-size:40px;padding-top:6px;'>⚖️</div>",
            unsafe_allow_html=True,
        )
    with col_title:
        st.markdown(
            "<div style='padding-top:4px;'>"
            "<p style='margin:0;font-size:20px;font-weight:700;color:#f8fafc;'>"
            "AI-Юрист по ЖКХ</p>"
            "<p style='margin:0;font-size:12px;color:#64748b;'>ПП РФ № 354</p>"
            "</div>",
            unsafe_allow_html=True,
        )
    with col_status:
        st.markdown(
            "<div style='display:flex;align-items:center;height:100%;padding-top:10px;'>"
            "<span style='background:#14532d;color:#4ade80;border-radius:12px;"
            "padding:4px 12px;font-size:13px;font-weight:600;'>"
            "🟢 Контекст квитанции подключен</span></div>",
            unsafe_allow_html=True,
        )
    with col_back:
        if st.button("← Вернуться к квитанции", key="chat_back"):
            st.session_state["active_screen"] = "analysis"
            st.rerun()

    st.divider()

    # --- Session state init ---
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if not st.session_state["chat_history"]:
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": _WELCOME_MESSAGE}
        )

    # --- Quick prompt chips ---
    st.markdown(
        "<p style='font-size:13px;color:#64748b;margin-bottom:6px;'>"
        "Быстрые вопросы:</p>",
        unsafe_allow_html=True,
    )
    chip_cols = st.columns(len(_QUICK_PROMPTS))
    triggered_prompt: str | None = None
    for idx, prompt_text in enumerate(_QUICK_PROMPTS):
        with chip_cols[idx]:
            if st.button(prompt_text, key=f"chip_{idx}"):
                triggered_prompt = prompt_text

    # --- Render message history ---
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- Handle quick-chip or text input ---
    user_input = st.chat_input("Задайте вопрос юристу...")
    prompt: str | None = triggered_prompt or (user_input if user_input else None)

    if prompt:
        # Display user message
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Stream assistant response
        comp_id = "cmp_2026_11"
        if st.session_state.get("analysis_result"):
            comp_id = st.session_state["analysis_result"].get("comparison_id", comp_id)

        with st.chat_message("assistant"):
            full_response = st.write_stream(
                client.chat_stream(comparison_id=comp_id, message=prompt)
            )

        st.session_state["chat_history"].append(
            {"role": "assistant", "content": full_response}
        )
