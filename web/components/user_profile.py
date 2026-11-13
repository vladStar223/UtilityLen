"""User profile and financial statistics component."""
import streamlit as st


def render_user_profile(client=None) -> None:
    """Render the user profile page with editable fields, financial metrics, and receipts registry."""
    if client is None:
        try:
            from api_client import get_api_client
            client = get_api_client()
        except Exception:
            client = None

    profile_data = {}
    stats_data = {}

    if client:
        try:
            profile_data = client.get_user_profile()
        except Exception:
            pass
        try:
            stats_data = client.get_user_stats()
        except Exception:
            pass

    # Default fallbacks
    profile = {
        "name": profile_data.get("name", "Иван Иванов"),
        "phone": profile_data.get("phone", "+7 (999) 000-00-00"),
        "email": profile_data.get("email", "ivan.ivanov@example.com"),
        "address": profile_data.get("address", "г. Владивосток, Океанский пр-кт, д. 28, кв. 14"),
        "account": profile_data.get("account", "1234567890"),
    }

    stats = {
        "total_bills": stats_data.get("total_bills", 142),
        "total_amount": stats_data.get("total_amount", 785400.0),
        "anomalies_found": stats_data.get("anomalies_found", 12),
        "savings_potential": stats_data.get("savings_potential", 24500.0),
    }

    st.markdown("## 👤 Личный кабинет")

    # 1. Profile Information Card
    with st.container():
        st.markdown("### Данные абонента")
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            name_val = st.text_input("Имя и Фамилия", value=profile["name"])
            phone_val = st.text_input("Номер телефона", value=profile["phone"])
            email_val = st.text_input("Email", value=profile["email"])
        with col_info2:
            address_val = st.text_input("Адрес объекта", value=profile["address"])
            account_val = st.text_input("Номер лицевого счета", value=profile["account"])
            st.write("")
            st.write("")
            if st.button("💾 Сохранить изменения", type="primary", use_container_width=True):
                new_data = {
                    "name": name_val,
                    "phone": phone_val,
                    "email": email_val,
                    "address": address_val,
                    "account": account_val,
                }
                if client:
                    client.update_user_profile(new_data)
                st.success("Данные профиля успешно обновлены!")

    st.markdown("---")

    # 2. Financial Statistics Cards
    st.markdown("### Финансовая статистика")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="📊 Всего проверено квитанций", value=str(stats["total_bills"]))

    with col2:
        st.metric(label="💳 Сумма проверенных начислений", value=f"{stats['total_amount']:,.2f} ₽")

    with col3:
        st.metric(label="🔍 Выявлено аномалий и нарушений", value=str(stats["anomalies_found"]))

    with col4:
        st.metric(label="💰 Потенциальная экономия", value=f"{stats['savings_potential']:,.2f} ₽")

    st.markdown("---")

    # 3. Receipts Registry
    st.markdown("### 📋 Реестр квитанций пользователя")

    registry = [
        {
            "id": "REC-2026-11-01",
            "date": "2026-11-10",
            "type": "Единый платежный документ (ЕПД)",
            "amount": 6700.0,
            "status": "Успешно проверено",
            "case_id": "case_epd_default",
        },
        {
            "id": "REC-2026-11-02",
            "date": "2026-11-05",
            "type": "Водоснабжение (ХВС / ГВС)",
            "amount": 569.18,
            "status": "Обнаружена аномалия (Коэфф. 1.5)",
            "case_id": "case_02_coeff_15",
        },
        {
            "id": "REC-2026-11-03",
            "date": "2026-11-02",
            "type": "Теплоснабжение (Отопление)",
            "amount": 6900.0,
            "status": "Внимание (Сезонный рост)",
            "case_id": "case_01_heating_spike",
        },
        {
            "id": "REC-2026-10-28",
            "date": "2026-10-28",
            "type": "Электроснабжение (Т1/Т2)",
            "amount": 1350.0,
            "status": "Успешно проверено",
            "case_id": "case_elec_default",
        },
    ]

    for item in registry:
        c1, c2, c3, c4, c5 = st.columns([1.5, 2.5, 1.5, 2.5, 1.5])
        with c1:
            st.write(item["date"])
        with c2:
            st.write(item["type"])
        with c3:
            st.write(f"**{item['amount']:,.2f} ₽**")
        with c4:
            if "аномалия" in item["status"].lower():
                st.markdown(f"<span style='color: #ef4444;'>● {item['status']}</span>", unsafe_allow_html=True)
            elif "внимание" in item["status"].lower():
                st.markdown(f"<span style='color: #f59e0b;'>● {item['status']}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span style='color: #10b981;'>● {item['status']}</span>", unsafe_allow_html=True)
        with c5:
            if st.button("Открыть", key=f"open_rec_{item['id']}", use_container_width=True):
                st.session_state["case_id"] = item["case_id"]
                st.session_state["analysis_result"] = None
                st.session_state["active_screen"] = "analysis"
                st.rerun()
