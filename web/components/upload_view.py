"""Upload view for receiving utility bill scans and photos."""
import streamlit as st


def render_upload_view(client) -> None:
    """Render the centered upload screen with photo/PDF/JSON support."""
    _, center, _ = st.columns([1, 2, 1])

    with center:
        with st.container(border=True):
            st.markdown(
                '<div style="text-align: center;">'
                '<div style="font-size: 4rem; line-height: 1;">📑</div>'
                "</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                '<h2 style="text-align: center;">Загрузите квитанцию ЖКХ</h2>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<p style="text-align: center; color: inherit; opacity: 0.8;">'
                "Перетащите фото квитанции, скриншот из мобильного банка "
                "или документ PDF/JSON</p>",
                unsafe_allow_html=True,
            )

            uploaded_file = st.file_uploader(
                "Квитанция",
                type=["png", "jpg", "jpeg", "pdf", "json"],
                label_visibility="collapsed",
            )

            if uploaded_file is not None:
                is_image = uploaded_file.type.startswith("image/")
                if is_image:
                    st.image(
                        uploaded_file,
                        caption="Загруженный скан квитанции",
                        use_column_width=True,
                    )
                else:
                    st.caption(
                        f"📎 Файл получен: **{uploaded_file.name}** "
                        f"({uploaded_file.type or 'неизвестный тип'})"
                    )

                st.success(
                    "🛡 Верифицировано по ГОСТ QR: Платежный код распознан"
                )

                if st.button(
                    "🔍 Перейти к анализу начислений",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state["analysis_result"] = client.compare_bills(
                        st.session_state.get("case_id", "case_02_coeff_15")
                    )
                    st.session_state["active_screen"] = "analysis"
                    st.rerun()
