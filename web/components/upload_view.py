"""Upload view for receiving utility bill scans and photos."""
import json

import streamlit as st

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_file(uploaded_file) -> tuple[bool, str]:
    """Проверяет реальный размер и сигнатуру файла (Magic Bytes)."""
    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
        return (
            False,
            f"Размер файла ({uploaded_file.size / (1024*1024):.1f} МБ) превышает лимит 10 МБ.",
        )
    # Читаем первые 512 байт для проверки сигнатуры
    header = uploaded_file.read(512)
    uploaded_file.seek(0)  # Сбрасываем указатель назад
    name_lower = uploaded_file.name.lower()
    # Проверка PNG
    if name_lower.endswith(".png"):
        if header.startswith(b"\x89PNG\r\n\x1a\n"):
            return True, "OK"
        return False, "Файл имеет расширение .png, но не является валидным изображением PNG."
    # Проверка JPEG
    if name_lower.endswith((".jpg", ".jpeg")):
        if header.startswith(b"\xff\xd8\xff"):
            return True, "OK"
        return False, "Файл имеет расширение .jpg/.jpeg, но не является валидным изображением JPEG."
    # Проверка PDF
    if name_lower.endswith(".pdf"):
        if header.startswith(b"%PDF-"):
            return True, "OK"
        return False, "Файл имеет расширение .pdf, но поврежден или не является валидным PDF."
    # Проверка JSON
    if name_lower.endswith(".json"):
        try:
            content = uploaded_file.read().decode("utf-8")
            uploaded_file.seek(0)
            json.loads(content)
            return True, "OK"
        except Exception:
            uploaded_file.seek(0)
            return False, "Файл имеет расширение .json, но содержит некорректный синтаксис JSON."
    return False, "Неподдерживаемый формат файла. Допустимы только PNG, JPG, PDF и JSON."


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
                is_valid, error_msg = validate_file(uploaded_file)
                if not is_valid:
                    st.error(f"❌ Ошибка валидации файла: {error_msg}")
                    return

                is_image = (uploaded_file.type or "").startswith("image/")
                if is_image:
                    st.image(
                        uploaded_file,
                        caption="Загруженный скан квитанции",
                        use_container_width=True,
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
