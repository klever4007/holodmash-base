import os
import psycopg2
from datetime import datetime
import streamlit as st

# Прописываем прямую ссылку на облачную базу данных Supabase, исключая Secrets
DB_URI = "postgresql://postgres:PXauRFl65nbNTZse@db.nnbgapxfwnigpmjypqem.supabase.co:5432/postgres"

def init_db():
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            fio TEXT, city TEXT, company TEXT, email TEXT, need TEXT, notes TEXT, image_url TEXT, created_at TEXT
        )
    """)
    conn.commit()
    return conn, cursor

# Настройка страницы
st.set_page_config(page_title="ХОЛОДМАШ | База клиентов", page_icon="❄️", layout="wide")

# Фирменный стиль Holodmash-Chiller (Скругления 12px, адаптивность, статус-бары)
st.markdown("""
    <style>
    /* Закругление краев для полей ввода */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 12px !important;
        border: 1px solid #0056B3 !important;
        background-color: #FAFAFA !important;
    }
    /* Стиль главной кнопки */
    .stButton>button {
        background-color: #0056B3 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        padding: 0.75rem !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003D82 !important;
        box-shadow: 0px 4px 10px rgba(0, 86, 179, 0.3);
    }
    /* Аккуратные карточки клиентов */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

st.title("❄️ ХОЛОДМАШ | Единая база клиентов")
st.caption("Профессиональный инструмент управления контрагентами. Синхронизация 24/7.")

try:
    conn, cursor = init_db()
except Exception as e:
    st.error(f"Ошибка подключения к базе данных Supabase: {e}")
    st.stop()

tab1, tab2 = st.tabs(["➕ Внести нового клиента", "🔍 Поиск и Выгрузка базы"])

with tab1:
    st.subheader("Форма добавления")
    col1, col2 = st.columns(2)
    
    with col1:
        fio = st.text_input("👤 ФИО представителя", placeholder="Иванов Иван Иванович")
        city = st.text_input("🌆 Город", placeholder="Москва")
        company = st.text_input("🏢 Компания / Организация", placeholder="ООО Холодмаш-Чиллер")
        email = st.text_input("✉️ Электронная почта (Email)", placeholder="info@holodmash-chiller.ru")
        
    with col2:
        need = st.text_area("🎯 Потребность (какой чиллер нужен / ТЗ)", placeholder="Хладоноситель, мощность, условия работы...")
        notes = st.text_area("📝 Важные рабочие заметки", placeholder="Договорились созвониться в пятницу...")
        
        st.markdown("**📸 Скриншот переписки (Ctrl+V или файл)**")
        uploaded_file = st.image_uploader("", label_visibility="collapsed")

    if st.button("🚀 Сохранить в облачную базу"):
        if not fio:
            st.error("Ошибка: Поле ФИО обязательно для заполнения!")
        else:
            image_data_url = "-"
            
            if uploaded_file is not None:
                import base64
                bytes_data = uploaded_file.getvalue()
                base64_str = base64.b64encode(bytes_data).decode("utf-8")
                file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else "image/png"
                image_data_url = f"data:{file_type};base64,{base64_str}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO contacts (fio, city, company, email, need, notes, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (fio, city, company, email, need, notes, image_data_url, now_str))
            conn.commit()
            st.success(f"✔️ Клиент '{fio}' успешно добавлен! Обновите вкладку поиска.")

with tab2:
    st.subheader("Глобальный архив")
    search = st.text_input("🔎 Быстрый фильтр по ФИО, Городу или Названию компании")
    
    if search:
        cursor.execute("""
            SELECT created_at, fio, city, company, email, need, notes, image_url 
            FROM contacts 
            WHERE fio ILIKE %s OR city ILIKE %s OR company ILIKE %s 
            ORDER BY id DESC LIMIT 1000
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT created_at, fio, city, company, email, need, notes, image_url FROM contacts ORDER BY id DESC LIMIT 100")
        
    records = cursor.fetchall()
    
    if records:
        import pandas as pd
        df = pd.DataFrame(records, columns=["Дата", "ФИО", "Город", "Компания", "Email", "Потребность", "Заметки", "Картинка"])
        df_excel = df.drop(columns=["Картинка"])
        csv = df_excel.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 Скачать текущую таблицу в Excel (CSV)",
            data=csv,
            file_name=f"baza_holodmash_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.markdown("---")

    for rec in records:
        with st.expander(f"📋 {rec[1]} | {rec[2]} ({rec[3]})"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**📅 Дата внесения:** {rec[0]}")
                st.markdown(f"**✉️ Электронная почта:** {rec[4]}")
                st.markdown(f"**🎯 Техническая потребность:**\n{rec[5]}")
                st.markdown(f"**📝 Рабочие заметки:**\n{rec[6]}")
            with c2:
                if rec[7] and rec[7] != "-":
                    st.markdown("**📸 Скриншот переписки:**")
                    st.image(rec[7], use_container_width=True)
                else:
                    st.caption("ℹ️ Скриншот не прикреплялся")

cursor.close()
conn.close()
import os
import psycopg2
from datetime import datetime
import streamlit as st

# Получаем строку подключения из настроек безопасности облака
DB_URI = st.secrets["postgres"]["uri"]

def init_db():
    conn = psycopg2.connect(DB_URI)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            fio TEXT, city TEXT, company TEXT, email TEXT, need TEXT, notes TEXT, image_url TEXT, created_at TEXT
        )
    """)
    conn.commit()
    return conn, cursor

# Настройка страницы с правильной кодировкой
st.set_page_config(page_title="ХОЛОДМАШ | База клиентов", page_icon="❄️", layout="wide")

# Фирменный стиль Holodmash-Chiller (Скругления 12px, адаптивность, статус-бары)
st.markdown("""
    <style>
    /* Закругление краев для полей ввода */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 12px !important;
        border: 1px solid #0056B3 !important;
        background-color: #FAFAFA !important;
    }
    /* Стиль главной кнопки */
    .stButton>button {
        background-color: #0056B3 !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: bold !important;
        width: 100%;
        padding: 0.75rem !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #003D82 !important;
        box-shadow: 0px 4px 10px rgba(0, 86, 179, 0.3);
    }
    /* Аккуратные карточки клиентов */
    div[data-testid="stExpander"] {
        border-radius: 12px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0px 2px 5px rgba(0,0,0,0.02);
    }
    </style>
""", unsafe_allow_html=True)

st.title("❄️ ХОЛОДМАШ | Единая база клиентов")
st.caption("Профессиональный инструмент управления контрагентами. Синхронизация 24/7.")

try:
    conn, cursor = init_db()
except Exception as e:
    st.error(f"Ошибка подключения к базе данных Supabase: {e}")
    st.stop()

tab1, tab2 = st.tabs(["➕ Внести нового клиента", "🔍 Поиск и Выгрузка базы"])

with tab1:
    st.subheader("Форма добавления")
    col1, col2 = st.columns(2)
    
    with col1:
        fio = st.text_input("👤 ФИО представителя", placeholder="Иванов Иван Иванович")
        city = st.text_input("🌆 Город", placeholder="Москва")
        company = st.text_input("🏢 Компания / Организация", placeholder="ООО Холодмаш-Чиллер")
        email = st.text_input("✉️ Электронная почта (Email)", placeholder="info@holodmash-chiller.ru")
        
    with col2:
        need = st.text_area("🎯 Потребность (какой чиллер нужен / ТЗ)", placeholder="Хладоноситель, мощность, условия работы...")
        notes = st.text_area("📝 Важные рабочие заметки", placeholder="Договорились созвониться в пятницу...")
        
        # ФИЧА: Вставка скриншота через Ctrl+V или файл
        st.markdown("**📸 Скриншот переписки (Ctrl+V или файл)**")
        uploaded_file = st.image_uploader("", label_visibility="collapsed")

    if st.button("🚀 Сохранить в облачную базу"):
        if not fio:
            st.error("Ошибка: Поле ФИО обязательно для заполнения!")
        else:
            image_data_url = "-"
            
            # Если юзер вставил картинку (через Ctrl+V или загрузил файл)
            if uploaded_file is not None:
                import base64
                # Переводим картинку в текст, чтобы она вечно хранилась прямо в базе данных без внешних дисков!
                bytes_data = uploaded_file.getvalue()
                base64_str = base64.b64encode(bytes_data).decode("utf-8")
                file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else "image/png"
                image_data_url = f"data:{file_type};base64,{base64_str}"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute("""
                INSERT INTO contacts (fio, city, company, email, need, notes, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (fio, city, company, email, need, notes, image_data_url, now_str))
            conn.commit()
            st.success(f"✔️ Клиент '{fio}' успешно добавлен! Обновите вкладку поиска.")

with tab2:
    st.subheader("Глобальный архив")
    search = st.text_input("🔎 Быстрый фильтр по ФИО, Городу или Названию компании")
    
    # Запрос данных
    if search:
        cursor.execute("""
            SELECT created_at, fio, city, company, email, need, notes, image_url 
            FROM contacts 
            WHERE fio ILIKE %s OR city ILIKE %s OR company ILIKE %s 
            ORDER BY id DESC LIMIT 1000
        """, (f'%{search}%', f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT created_at, fio, city, company, email, need, notes, image_url FROM contacts ORDER BY id DESC LIMIT 100")
        
    records = cursor.fetchall()
    
    # ФИЧА: Кнопка выгрузки в Excel/CSV для чилла
    if records:
        import pandas as pd
        df = pd.DataFrame(records, columns=["Дата", "ФИО", "Город", "Компания", "Email", "Потребность", "Заметки", "Картинка"])
        # Убираем огромный код картинки из файла эксель, чтобы он весил мало
        df_excel = df.drop(columns=["Картинка"])
        csv = df_excel.to_csv(index=False).encode('utf-8-sig')
        
        st.download_button(
            label="📥 Скачать текущую таблицу в Excel (CSV)",
            data=csv,
            file_name=f"baza_holodmash_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
        st.markdown("---")

    # Вывод карточек
    for rec in records:
        with st.expander(f"📋 {rec[1]} | {rec[3]} ({rec[2]})"):
            c1, c2 = st.columns([3, 2])
            with c1:
                st.markdown(f"**📅 Дата внесения:** {rec[0]}")
                st.markdown(f"**✉️ Электронная почта:** {rec[4]}")
                st.markdown(f"**🎯 Техническая потребность:**\n{rec[5]}")
                st.markdown(f"**📝 Рабочие заметки:**\n{rec[6]}")
            with c2:
                if rec[7] and rec[7] != "-":
                    st.markdown("**📸 Скриншот переписки:**")
                    st.image(rec[7], use_container_width=True)
                else:
                    st.caption("ℹ️ Скриншот не прикреплялся")

cursor.close()
conn.close()
