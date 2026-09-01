import os
import sqlite3
import streamlit as st
import pandas as pd
import io

DB_FILE = "storage.db"

# Настройка страницы
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
search = st.text_input("🔎 Быстрый поиск (ФИО, Город или Компания)")
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
                # 1. Формируем таблицу данных
                df = pd.DataFrame(records, columns=[
                    "Дата создания", "ФИО", "Город", "Компания", "Email", 
                    "Потребность", "Заметки", "Картинка", "Телефон", 
                    "Дата звонка", "Перезвонить", "Написать"
                ])
                
                # Удаляем картинку из выгрузки
                df_excel = df.drop(columns=["Картинка"])
                
                # Смена порядка колонок для логичности в Excel
                df_excel = df_excel[[
                    "Дата создания", "ФИО", "Телефон", "Email", "Город", "Компания", 
                    "Потребность", "Заметки", "Дата звонка", "Перезвонить", "Написать"
                ]]

                # 2. Создаем красивый структурированный файл Excel в памяти
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_excel.to_excel(writer, index=False, sheet_name=cat[:30])
                    
                    # Прокачиваем визуальный стиль колонок
                    workbook = writer.book
                    worksheet = writer.sheets[cat[:30]]
                    
                    # Делаем автоподбор ширины под контент, чтобы текст не обрезался
                    for col in worksheet.columns:
                        max_len = max(len(str(cell.value or '')) for cell in col)
                        col_letter = col[0].column_letter
                        worksheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

                excel_data = buffer.getvalue()
                
                # 3. Кнопка скачивания НАСТОЯЩЕГО Excel (.xlsx)
                st.download_button(
                    label=f"📥 Скачать список '{cat}' в EXCEL (.xlsx)",
                    data=excel_data,
                    file_name=f"baza_{cat}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_{i}"
                )
                st.markdown("---")
                
                # Вывод карточек на экран
                for rec in records:
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
            st.info("Ожидание внесения новых данных для синхронизации колонок графика.")

conn.close()
