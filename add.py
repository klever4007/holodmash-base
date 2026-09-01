import os
import sqlite3
from datetime import datetime
import streamlit as st
from PIL import Image

DB_FILE = "storage.db"
PHOTO_DIR = "photos"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fio TEXT, city TEXT, company TEXT, email TEXT, need TEXT, notes TEXT, image_note TEXT, created_at TEXT
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fio ON contacts(fio);")
    conn.commit()
    return conn

# Фирменный стиль в цветах Holodmash-Chiller (Глубокий синий, стальной, закругления углов)
st.set_page_config(page_title="Холодмаш | Блокнот База", page_icon="??", layout="wide")

st.markdown("""
    <style>
    /* Главный фон и скругления для полей ввода */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px !important;
        border: 1px solid #1E3A8A !important;
    }
    /* Стиль кнопок */
    .stButton>button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 0.5rem 2rem !important;
    }
    .stButton>button:hover {
        background-color: #3B82F6 !important;
    }
    /* Стиль карточек */
    .css-1r6g72h, .stExpander {
        border-radius: 8px !important;
        border: 1px solid #E2E8F0 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("?? ХОЛОДМАШ | База Данных Клиентов")
st.caption("Профессиональный блокнот-инструмент для управления записями")

conn = init_db()
cursor = conn.cursor()

tab1, tab2 = st.tabs(["? Добавить запись", "?? Быстрый просмотр"])

with tab1:
    st.subheader("Внесение нового контрагента")
    col1, col2 = st.columns(2)
    
    with col1:
        fio = st.text_input("ФИО представителя", placeholder="Иванов Иван Иванович")
        city = st.text_input("Город", placeholder="Москва")
        company = st.text_input("Компания / Организация", placeholder="ООО Холодмаш-Чиллер")
        email = st.text_input("Электронная почта (Email)", placeholder="info@holodmash-chiller.ru")
        
    with col2:
        need = st.text_area("Потребность / Проект чиллера", placeholder="Технические характеристики, хладоноситель...")
        notes = st.text_area("Рабочие заметки", placeholder="Важные комментарии по сделке...")
        uploaded_file = st.file_uploader("Скриншот переписки (JPEG / PNG)", type=["jpg", "jpeg", "png"])

    if st.button("Сохранить в базу"):
        if not fio:
            st.error("Пожалуйста, заполните поле ФИО.")
        else:
            img_note = "Фото отсутствует"
            if uploaded_file is not None:
                if not os.path.exists(PHOTO_DIR): os.makedirs(PHOTO_DIR)
                ext = os.path.splitext(uploaded_file.name)[1]
                filename = f"chat_{int(datetime.now().timestamp())}{ext}"
                img_dest = os.path.join(PHOTO_DIR, filename)
                
                image = Image.open(uploaded_file)
                image.save(img_dest)
                img_note = img_dest

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO contacts (fio, city, company, email, need, notes, image_note, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (fio, city, company, email, need, notes, img_note, now_str))
            conn.commit()
            st.success(f"?? Запись для {fio} успешно добавлена в систему.")

with tab2:
    st.subheader("Поиск по архиву")
    search = st.text_input("?? Введите имя, город или компанию для фильтрации")
    
    if search:
        cursor.execute("SELECT created_at, fio, city, company, email, need, notes, image_note FROM contacts WHERE fio LIKE ? OR city LIKE ? OR company LIKE ? ORDER BY id DESC LIMIT 1000", (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT created_at, fio, city, company, email, need, notes, image_note FROM contacts ORDER BY id DESC LIMIT 100")
        
    records = cursor.fetchall()
    
    for rec in records:
        with st.expander(f"?? {rec[1]} | {rec[3]} ({rec[2]})"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Дата внесения:** {rec[0]}")
                st.markdown(f"**Почта:** {rec[4]}")
                st.markdown(f"**Потребность:** {rec[5]}")
                st.markdown(f"**Заметки:** {rec[6]}")
            with c2:
                if rec[7] != "Фото отсутствует" and os.path.exists(rec[7]):
                    st.image(rec[7], caption="Скриншот истории переписки", use_container_width=True)
                else:
                    st.caption("?? Изображение к данной записи не прикреплено")
conn.close()
