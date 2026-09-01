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
    fio = st.text_input("ФИО представителя *", placeholder="Иванов Иван Иванович", key="page_add_fio")
    city = st.text_input("🌆 Город", placeholder="Москва", key="page_add_city")
    company = st.text_input("🏢 Компания / Организация", placeholder="ООО Холодмаш-Чиллер", key="page_add_company")
    category = st.selectbox("⚙️ Направление оборудования", options=CATEGORIES, index=1, key="page_add_category")
    
with col2:
    st.markdown("##### 📞 Контакты (можно пропустить)")
    phone = st.text_input("📱 Номер телефона", placeholder="+7 (999) 000-00-00", key="page_add_phone")
    email = st.text_input("✉️ Электронная почта (Email)", placeholder="info@holodmash-chiller.ru", key="page_add_email")
    need = st.text_area("🎯 Потребность (ТЗ)", placeholder="Хладоноситель, мощность...", height=115, key="page_add_need")
    
with col3:
    st.markdown("##### 📅 График связи и заметки")
    notes = st.text_area("📝 Важные рабочие заметки", placeholder="Комментарии...", height=50, key="page_add_notes")
    
    use_dates = st.checkbox("🗓️ Зафиксировать даты звонков / писем", key="page_add_use_dates")
    call_date_str, callback_date_str, msg_date_str = "-", "-", "-"
    
    if use_dates:
        d1 = st.date_input("📞 Когда звонили", value=datetime.today(), key="page_add_d1")
        d2 = st.date_input("⏳ Когда перезвонить", value=datetime.today(), key="page_add_d2")
        d3 = st.date_input("💬 Когда отправить сообщение", value=datetime.today(), key="page_add_d3")
        call_date_str, callback_date_str, msg_date_str = d1.strftime("%Y-%m-%d"), d2.strftime("%Y-%m-%d"), d3.strftime("%Y-%m-%d")
        
    st.markdown("**📸 Скриншот переписки**")
    uploaded_file = st.file_uploader("", label_visibility="collapsed", type=["jpg", "jpeg", "png"], key="page_add_uploader")

if st.button("🚀 Сохранить в базу", key="page_add_submit"):
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
import os
import sqlite3
import streamlit as st
import pandas as pd
import io

DB_FILE = "storage.db"

st.set_page_config(page_title="ХОЛОДМАШ | Архив", page_icon="🔍", layout="wide")

st.markdown("""
    <style>
    .stTextInput>div>div>input { border-radius: 12px !important; border: 1px solid #0056B3 !important; background-color: #FAFAFA !important; }
    div[data-testid="stExpander"] { border-radius: 12px !important; border: 1px solid #E2E8F0 !important; background-color: #FFFFFF !important; }
    .stButton>button { background-color: #28A745 !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 ХОЛОДМАШ | Глобальный архив с фильтрацией")
st.caption("Поиск контрагентов и выгрузка красивых отчетов в Excel по направлениям.")

if not os.path.exists(DB_FILE):
    st.info("База данных пока пуста. Внесите первого клиента через форму добавления.")
    st.stop()

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

CATEGORIES = ["Спиральное оборудование", "Чиллеры", "Транспортеры", "Другое"]
search = st.text_input("🔎 Быстрый поиск (ФИО, Город или Компания)", key="page_view_search_input")
sub_tabs = st.tabs([f"📦 {cat}" for cat in CATEGORIES])

for i, cat in enumerate(CATEGORIES):
    with sub_tabs[i]:
        try:
            if search:
                cursor.execute("""
                    SELECT created_at, fio, city, company, email, need, notes, image_url, phone, call_date, callback_date, msg_date 
                    FROM contacts 
                    WHERE (category = ? OR (category IS NULL AND ? = 'Другое')) AND (fio LIKE ? OR city LIKE ? OR company LIKE ?)
                    ORDER BY id DESC LIMIT 1000
                """, (cat, cat, f'%{search}%', f'%{search}%', f'%{search}%'))
            else:
                cursor.execute("""
                    SELECT created_at, fio, city, company, email, need, notes, image_url, phone, call_date, callback_date, msg_date 
                    FROM contacts 
                    WHERE category = ? OR (category IS NULL AND ? = 'Другое')
                    ORDER BY id DESC LIMIT 500
                """, (cat, cat))
                
            records = cursor.fetchall()
            
            if records:
                df = pd.DataFrame(records, columns=["Дата создания", "ФИО", "Город", "Компания", "Email", "Потребность", "Заметки", "Картинка", "Телефон", "Дата звонка", "Перезвонить", "Написать"])
                df_excel = df.drop(columns=["Картинка"])
                df_excel = df_excel[["Дата создания", "ФИО", "Телефон", "Email", "Город", "Компания", "Потребность", "Заметки", "Дата звонка", "Перезвонить", "Написать"]]

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name=cat[:30])
                    workbook = writer.book
                    worksheet = writer.sheets[cat[:30]]
                    for col in worksheet.columns:
                        max_len = max(len(str(cell.value or '')) for cell in col)
                        col_letter = col.column_letter
                        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

                excel_data = buffer.getvalue()
                
                st.download_button(
                    label=f"📥 Скачать список '{cat}' в EXCEL (.xlsx)",
                    data=excel_data,
                    file_name=f"baza_{cat}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"page_view_dl_btn_{i}"
                )
                st.markdown("---")
                
                for idx, rec in enumerate(records):
                    rec_date, rec_fio, rec_city, rec_company, rec_email, rec_need, rec_notes, rec_image, rec_phone, rec_call, rec_callback, rec_msg = rec
                    title_text = f"📋 {rec_fio or 'Без имени'} | {rec_company or 'Без компании'} ({rec_city or 'Город не указан'})"
                    
                    with st.expander(title_text):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(f"**📅 Дата внесения:** {rec_date}")
                            if rec_phone and rec_phone != "-":
                                st.markdown(f"**📱 Номер телефона:** {rec_phone}")
                            if rec_email and rec_email != "-":
                                st.markdown(f"**✉️ Электронная почта:** {rec_email}")
                            st.markdown(f"**🎯 Техническая потребность:**\n{rec_need or '—'}")
                            st.markdown(f"**📝 Рабочие заметки:**\n{rec_notes or '—'}")
                            if rec_call and rec_call != "-":
                                st.markdown(f"**📞 Когда звонили:** {rec_call}")
                            if rec_callback and rec_callback != "-":
                                st.markdown(f"**⏳ Когда перезвонить:** {rec_callback}")
                            if rec_msg and rec_msg != "-":
                                st.markdown(f"**💬 Когда отправить сообщение:** {rec_msg}")
                        with c2:
                            if isinstance(rec_image, str) and rec_image.startswith("data:image"):
                                st.markdown("**📸 Скриншот переписки:**")
                                try:
                                    st.image(rec_image, use_container_width=True)
                                except Exception:
                                    st.caption("⚠️ Ошибка отображения скриншота")
                            else:
                                st.caption("ℹ️ Скриншот отсутствует")
            else:
                st.info(f"В направлении '{cat}' пока нет записей.")
        except sqlite3.OperationalError:
            st.info("Ожидание внесения новых данных...")

conn.close()
