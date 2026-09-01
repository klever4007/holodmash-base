import os
import sqlite3
import base64
from datetime import datetime
import streamlit as st

DB_FILE = "storage.db"

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT, city TEXT, company TEXT, email TEXT, need TEXT, notes TEXT, 
            image_url TEXT, created_at TEXT, category TEXT,
            phone TEXT, call_date TEXT, callback_date TEXT, msg_date TEXT
        )
    """)
    alter_columns = {
        "category": "TEXT", "phone": "TEXT", "call_date": "TEXT", 
        "callback_date": "TEXT", "msg_date": "TEXT"
    }
    for col, col_type in alter_columns.items():
        try:
            cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass
    conn.commit()
    return conn, cursor

st.set_page_config(page_title="ХОЛОДМАШ | Добавление", page_icon="❄️", layout="wide")

# Фирменный стиль Holodmash-Chiller
st.markdown("""
    <style>
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div, .stDateInput>div>div>input {
        border-radius: 12px !important; border: 1px solid #0056B3 !important; background-color: #FAFAFA !important;
    }
    .stButton>button {
        background-color: #0056B3 !important; color: white !important;
        border-radius: 12px !important; border: none !important;
        font-weight: bold !important; width: 100%; padding: 0.75rem !important;
    }
    .stButton>button:hover { background-color: #003D82 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("❄️ ХОЛОДМАШ | Внести нового клиента")
st.caption("Форма мгновенной фиксации контрагентов. Синхронизация 24/7.")

try:
    conn, cursor = init_db()
except Exception as e:
    st.error(f"Ошибка базы данных: {e}")
    st.stop()

CATEGORIES = ["Спиральное оборудование", "Чиллеры", "Транспортеры", "Другое"]

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("##### 👤 Основные данные")
    fio = st.text_input("ФИО представителя *", placeholder="Иванов Иван Иванович", key="add_fio")
    city = st.text_input("🌆 Город", placeholder="Москва", key="add_city")
    company = st.text_input("🏢 Компания / Организация", placeholder="ООО Холодмаш-Чиллер", key="add_company")
    category = st.selectbox("⚙️ Направление оборудования", options=CATEGORIES, index=1, key="add_category")
    
with col2:
    st.markdown("##### 📞 Контакты (можно пропустить)")
    phone = st.text_input("📱 Номер телефона", placeholder="+7 (999) 000-00-00", key="add_phone")
    email = st.text_input("✉️ Электронная почта (Email)", placeholder="info@holodmash-chiller.ru", key="add_email")
    need = st.text_area("🎯 Потребность (ТЗ)", placeholder="Хладоноситель, мощность...", height=115, key="add_need")
    
with col3:
    st.markdown("##### 📅 График связи и заметки")
    notes = st.text_area("📝 Важные рабочие заметки", placeholder="Комментарии...", height=50, key="add_notes")
    
    use_dates = st.checkbox("🗓️ Зафиксировать даты звонков / писем", key="add_use_dates")
    call_date_str, callback_date_str, msg_date_str = "-", "-", "-"
    
    if use_dates:
        d1 = st.date_input("📞 Когда звонили", value=datetime.today(), key="add_d1")
        d2 = st.date_input("⏳ Когда перезвонить", value=datetime.today(), key="add_d2")
        d3 = st.date_input("💬 Когда отправить сообщение", value=datetime.today(), key="add_d3")
        call_date_str, callback_date_str, msg_date_str = d1.strftime("%Y-%m-%d"), d2.strftime("%Y-%m-%d"), d3.strftime("%Y-%m-%d")
        
    st.markdown("**📸 Скриншот переписки**")
    uploaded_file = st.file_uploader("", label_visibility="collapsed", type=["jpg", "jpeg", "png"], key="add_uploader")

if st.button("🚀 Сохранить в базу", key="add_submit_btn"):
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
        cursor.execute("""
            INSERT INTO contacts (fio, city, company, email, need, notes, image_url, created_at, category, phone, call_date, callback_date, msg_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fio, city, company, email if email else "-", need, notes, image_data_url, now_str, category, phone if phone else "-", call_date_str, callback_date_str, msg_date_str))
        conn.commit()
        st.success(f"✔️ Клиент '{fio}' успешно добавлен!")

conn.close()
