import os
import base64
from datetime import datetime
import streamlit as st
import pandas as pd

# Настройка страницы
st.set_page_config(page_title="ХОЛОДМАШ | База клиентов", page_icon="❄️", layout="wide")

# Фирменный стиль Holodmash-Chiller (Скругления 12px)
st.markdown("""
    <style>
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div {
        border-radius: 12px !important;
        border: 1px solid #0056B3 !important;
        background-color: #FAFAFA !important;
    }
    .stButton>button {
        background-color: #0056B3 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        padding: 0.75rem !important;
    }
    .stButton>button:hover {
        background-color: #003D82 !important;
    }
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("❄️ ХОЛОДМАШ | Единая база клиентов")
st.caption("Профессиональный инструмент управления контрагентами по направлениям. Синхронизация 24/7.")

# Подключение к облачной базе Supabase через Streamlit Secrets
try:
    conn = st.connection("postgres", type="sql")
except Exception as e:
    st.error(f"Ошибка подключения к Supabase: {e}")
    st.stop()

tab1, tab2 = st.tabs(["➕ Внести нового клиента", "🔍 Поиск по направлениям"])

CATEGORIES = ["Спиральное оборудование", "Чиллеры", "Транспортеры", "Другое"]

with tab1:
    st.subheader("Форма добавления")
    col1, col2 = st.columns(2)
    
    with col1:
        fio = st.text_input("👤 ФИО представителя", placeholder="Иванов Иван Иванович")
        city = st.text_input("🌆 Город", placeholder="Москва")
        company = st.text_input("🏢 Компания / Организация", placeholder="ООО Холодмаш-Чиллер")
        email = st.text_input("✉️ Электронная почта (Email)", placeholder="info@holodmash-chiller.ru")
        
    with col2:
        category = st.selectbox("⚙️ Направление оборудования", options=CATEGORIES, index=1)
        need = st.text_area("🎯 Потребность (ТЗ)", placeholder="Хладоноситель, мощность...")
        notes = st.text_area("📝 Важные рабочие заметки", placeholder="Комментарии...")
        
        st.markdown("**📸 Скриншот переписки (Ctrl+V или файл)**")
        uploaded_file = st.file_uploader("", label_visibility="collapsed", type=["jpg", "jpeg", "png"])

    if st.button("🚀 Сохранить в базу"):
        if not fio:
            st.error("Ошибка: Поле ФИО обязательно для заполнения!")
        else:
            image_data_url = "-"
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                base64_str = base64.b64encode(bytes_data).decode("utf-8")
                file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else "image/png"
                image_data_url = f"data:{file_type};base64,{base64_str}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Запись в Supabase (PostgreSQL использует синтаксис :имя_переменной)
            with conn.session as session:
                query = """
                    INSERT INTO contacts (fio, city, company, email, need, notes, image_url, created_at, category)
                    VALUES (:fio, :city, :company, :email, :need, :notes, :image_url, :created_at, :category)
                """
                session.execute(
                    query, 
                    dict(fio=fio, city=city, company=company, email=email, need=need, notes=notes, image_url=image_data_url, created_at=now_str, category=category)
                )
                session.commit()
            st.success(f"✔️ Клиент '{fio}' успешно добавлен в направление '{category}'!")

with tab2:
    st.subheader("Глобальный архив с фильтрацией")
    search = st.text_input("🔎 Быстрый поиск (ФИО, Город или Компания)")
    sub_tabs = st.tabs([f"📦 {cat}" for cat in CATEGORIES])
    
    for i, cat in enumerate(CATEGORIES):
        with sub_tabs[i]:
            # Поиск в Supabase
            if search:
                query = """
                    SELECT created_at, fio, city, company, email, need, notes, image_url 
                    FROM contacts 
                    WHERE (category = :cat OR (category IS NULL AND :cat = 'Другое')) 
                      AND (fio ILIKE :search OR city ILIKE :search OR company ILIKE :search)
                    ORDER BY id DESC LIMIT 1000
                """
                df = conn.query(query, params=dict(cat=cat, search=f"%{search}%"))
            else:
                query = """
                    SELECT created_at, fio, city, company, email, need, notes, image_url 
                    FROM contacts 
                    WHERE category = :cat OR (category IS NULL AND :cat = 'Другое')
                    ORDER BY id DESC LIMIT 500
                """
                df = conn.query(query, params=dict(cat=cat))
            
            if not df.empty:
                # Подготовка Excel версии (удаляем тяжелую графику)
                df_excel = df.drop(columns=["image_url"], errors="ignore")
                csv = df_excel.to_csv(index=False).encode('utf-8-sig')
                
                st.download_button(
                    label=f"📥 Скачать список '{cat}' в Excel",
                    data=csv,
                    file_name=f"baza_{cat}.csv",
                    mime="text/csv",
                    key=f"dl_{i}"
                )
                st.markdown("---")
                
                # Построчный вывод карточек через итерацию DataFrame
                for _, row in df.iterrows():
                    c_fio = row.get('fio')
                    c_company = row.get('company')
                    c_city = row.get('city')
                    
                    with st.expander(f"📋 {c_fio or 'Без имени'} | {c_company or 'Без компании'} ({c_city or 'Город не указан'})"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**📅 Дата внесения:** {row.get('created_at')}")
                            st.markdown(f"**✉️ Электронная почта:** {row.get('email') or '—'}")
                            st.markdown(f"**🎯 Техническая потребность:**\n{row.get('need') or '—'}")
                            st.markdown(f"**📝 Рабочие заметки:**\n{row.get('notes') or '—'}")
                        with c2:
                            c_image = row.get('image_url')
                            if isinstance(c_image, str) and c_image.startswith("data:image"):
                                st.markdown("**📸 Скриншот переписки:**")
                                try:
                                    st.image(c_image, use_container_width=True)
                                except Exception:
                                    st.caption("⚠️ Ошибка отображения скриншота")
                            else:
                                st.caption("ℹ️ Скриншот отсутствует")
            else:
                st.info(f"В направлении '{cat}' пока нет записей.")
