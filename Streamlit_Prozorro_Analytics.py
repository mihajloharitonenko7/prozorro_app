import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
import os

st.set_page_config(page_title="Порівняльна аналітика Prozorro", layout="wide")

# --- Загрузка CSV з тієї ж папки ------------------------------------------------
csv_file = 'prozorro_data.csv'
if not os.path.exists(csv_file):
    st.error(f"Файл {csv_file} не знайдено в поточній папці!")
    st.stop()

try:
    df = pd.read_csv(csv_file, low_memory=False)
except Exception as e:
    st.error(f"Не вдалося прочитати CSV: {e}")
    st.stop()

# --- Призначення колонок за назвами CSV ----------------------------------------
buyer_col = 'supplierName'
amount_col = "valueAmount"
participants_col = "supplierID"  
buyer_col = "disposerName"
region_col = "disposerID"         
category_col = "description"
date_col = "dateSigned"

# --- Підготовка робочого DataFrame ---------------------------------------------
work = df.copy()
work['_amount'] = pd.to_numeric(work[amount_col], errors='coerce')
work['_participants'] = pd.to_numeric(work[participants_col], errors='coerce') if participants_col else np.nan
work['_date'] = pd.to_datetime(work[date_col], errors='coerce') if date_col else pd.NaT

# --- Вивід основних даних ------------------------------------------------------
st.title('Порівняльна аналітика державних закупівель — Prozorro')
st.subheader('Перші 10 рядків CSV')
st.dataframe(work.head(10))

# --- Метрики -------------------------------------------------------------------
total_sum = work['_amount'].sum(min_count=1)
st.metric('Загальна сума контрактів', f"{total_sum:,.2f}" if not pd.isna(total_sum) else 'N/A')
if work['_participants'].notna().any():
    avg_participants = work['_participants'].mean()
    st.metric('Середня конкуренція (учасники)', f"{avg_participants:.2f}")

# --- Фільтри -------------------------------------------------------------------
st.header('Фільтри')
filter_cols = st.columns(3)
with filter_cols[0]:
    if buyer_col:
        buyer_options = ['(усі)'] + sorted(work[buyer_col].dropna().unique())
        buyer_sel = st.selectbox('Замовник', buyer_options, index=0)
    else:
        buyer_sel = '(усі)'
with filter_cols[1]:
    if region_col:
        region_options = ['(усі)'] + sorted(work[region_col].dropna().unique())
        region_sel = st.selectbox('Регіон', region_options, index=0)
    else:
        region_sel = '(усі)'
with filter_cols[2]:
    if category_col:
        category_options = ['(усі)'] + sorted(work[category_col].dropna().unique())
        category_sel = st.selectbox('Категорія', category_options, index=0)
    else:
        category_sel = '(усі)'

# --- Застосування фільтрів ---------------------------------------------------
mask = pd.Series(True, index=work.index)
if buyer_sel != '(усі)' and buyer_col:
    mask &= work[buyer_col] == buyer_sel
if region_sel != '(усі)' and region_col:
    mask &= work[region_col] == region_sel
if category_sel != '(усі)' and category_col:
    mask &= work[category_col] == category_sel

filtered = work[mask].copy()
st.write(f'Показано рядків: {len(filtered)} з {len(work)}')

# --- Візуалізації ---------------------------------------------------------------
st.header('Візуалізації')

# Сума контрактів за категоріями
if category_col:
    agg = filtered.groupby(category_col)['_amount'].sum().reset_index().sort_values('_amount', ascending=False)
    fig = px.bar(agg, x=category_col, y='_amount', title='Сума контрактів за категоріями', labels={'_amount':'Сума'})
    st.plotly_chart(fig, use_container_width=True)

# Розподіл кількості учасників
if filtered['_participants'].notna().any():
    fig2 = px.histogram(filtered, x='_participants', nbins=20, title='Розподіл кількості учасників')
    st.plotly_chart(fig2, use_container_width=True)
    st.write(filtered['_participants'].describe().to_frame().T)

# --- Експорт ------------------------------------------------------------------
st.header('Експорт результатів')
from io import BytesIO

def to_excel_bytes(df_to_save):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_to_save.to_excel(writer, index=False, sheet_name='filtered')
        writer.save()
    return output.getvalue()

if st.button('Завантажити фільтровані дані (Excel)'):
    if len(filtered) == 0:
        st.warning('Немає даних для завантаження')
    else:
        data_xls = to_excel_bytes(filtered)
        st.download_button('Завантажити Excel', data=data_xls, file_name='prozorro_filtered.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
