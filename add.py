import os
import base64
import psycopg2
from datetime import datetime
import streamlit as st
import pandas as pd

# 1. НАСТРОЙКА СТРАНИЦЫ
st.set_page_config(page_title="ХОЛОДМАШ | База клиентов", page_icon="❄️", layout="wide")

# 2. ФИРМЕННЫЙ СТИЛЬ HOLODMASH-CHILLER (Скругления 12px)
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

# 3. ПОДКЛЮЧЕНИЕ К ОБЛАЧНОЙ БАЗЕ SUPABASE
@st.cache_resource
def get_connection():
    try:
        # Автоматически считывает исправленный URI из Advanced settings -> Secrets
        conn_uri = st.secrets["postgres"]["uri"]
        return psycopg2.connect(conn_uri)
    except Exception as e:
        st.error(f"Ошибка подключения к базе Supabase: {e}")
        return None

conn = get_connection()

# Если база не ответила, аварийно останавливаем работу интерфейса
if conn is None:
    st.stop()

# 4. СОЗДАНИЕ ВКЛАДОК И КАТЕГОРИЙ
tab1, tab2 = st.tabs(["➕ Внести нового клиента", "🔍 Поиск по направлениям"])

CATEGORIES = ["Спиральное оборудование", "Чиллеры", "Транспортеры", "Другое"]

# ==================== ВКЛАДКА 1: ДОБАВЛЕНИЕ КЛИЕНТА ====================
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
            
            try:
                with conn.cursor() as cursor:
                    query = """
                        INSERT INTO contacts (fio, city, company, email, need, notes, image_url, created_at, category)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (fio, city, company, email, need, notes, image_data_url, now_str, category))
                    conn.commit()
                st.success(f"✔️ Клиент '{fio}' успешно добавлен в направление '{category}'!")
            except Exception as e:
                st.error(f"Ошибка при сохранении: {e}")
                conn.rollback()

# ==================== ВКЛАДКА 2: ПОИСК И АРХИВ ====================
with tab2:
    st.subheader("Глобальный архив с фильтрацией")
    search = st.text_input("🔎 Быстрый поиск (ФИО, Город или Компания)")
    sub_tabs = st.tabs([f"📦 {cat}" for cat in CATEGORIES])
    
    for i, cat in enumerate(CATEGORIES):
        with sub_tabs[i]:
            try:
                with conn.cursor() as cursor:
                    # Если пользователь использует строку поиска
                    if search:
                        query = """
                            SELECT created_at, fio, city, company, email, need, notes, image_url 
                            FROM contacts 
                            WHERE (category = %s OR (category IS NULL AND %s = 'Другое')) 
                              AND (fio ILIKE %s OR city ILIKE %s OR company ILIKE %s)
                            ORDER BY id DESC LIMIT 1000
                        """
                        search_param = f"%{search}%"
                        cursor.execute(query, (cat, cat, search_param, search_param, search_param))
                    # Если поиск пустой — выгружаем последние записи категории
                    else:
                        query = """
                            SELECT created_at, fio, city, company, email, need, notes, image_url 
                            FROM contacts 
                            WHERE category = %s OR (category IS NULL AND %s = 'Другое')
                            ORDER BY id DESC LIMIT 500
                        """
                        cursor.execute(query, (cat, cat))
                    
                    records = cursor.fetchall()
                
                # Если в этой вкладке есть данные
                if records:
                    # Формируем Excel/CSV отчет
                    df = pd.DataFrame(records, columns=["Дата", "ФИО", "Город", "Компания", "Email", "Потребность", "Заметки", "Картинка"])
                    df_excel = df.drop(columns=["Картинка"], errors="ignore")
                    csv = df_excel.to_csv(index=False).encode('utf-8-sig')
                    
                    st.download_button(
                        label=f"📥 Скачать список '{cat}' в Excel",
                        data=csv,
                        file_name=f"baza_{cat}.csv",
                        mime="text/csv",
                        key=f"dl_{i}"
                    )
                    st.markdown("---")
                    
                    # Разворачиваем карточки клиентов на экране
                    for rec in records:
                        c_date, c_fio, c_city, c_company, c_email, c_need, c_notes, c_image = rec
                        
                        with st.expander(f"📋 {c_fio or 'Без имени'} | {c_company or 'Без компании'} ({c_city or 'Город не указан'})"):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"**📅 Дата внесения:** {c_date}")
                                st.markdown(f"**✉️ Электронная почта:** {c_email or '—'}")
                                st.markdown(f"**🎯 Техническая потребность:**\n{c_need or '—'}")
                                st.markdown(f"**📝 Рабочие заметки:**\n{c_notes or '—'}")
                            with c2:
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
            except Exception as e:
                st.error(f"Ошибка при получении данных: {e}")
                conn.rollback()
