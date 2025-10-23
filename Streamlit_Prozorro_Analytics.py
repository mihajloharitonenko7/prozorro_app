import streamlit as st
import pandas as pd
import plotly.express as px
import os

file_path = os.path.join(os.path.dirname(__file__), "prozorro_data.csv")

work = pd.read_csv(file_path)

expected_cols = ["tender_id", "procuring_entity", "region", "category", "value", "participants"]

missing = [col for col in expected_cols if col not in work.columns]
if missing:
    st.error(f"❌ Відсутні колонки у файлі: {missing}")
    st.stop()

work["_value"] = pd.to_numeric(work["value"], errors="coerce")
work["_participants"] = pd.to_numeric(work["participants"], errors="coerce")

st.title("📊 Порівняльна аналітика державних закупівель (Prozorro)")

region_filter = st.multiselect("🌍 Обери регіон:", sorted(work["region"].unique()))
category_filter = st.multiselect("📦 Обери категорію:", sorted(work["category"].unique()))
buyer_filter = st.multiselect("🏢 Обери замовника:", sorted(work["procuring_entity"].unique()))

filtered = work.copy()
if region_filter:
    filtered = filtered[filtered["region"].isin(region_filter)]
if category_filter:
    filtered = filtered[filtered["category"].isin(category_filter)]
if buyer_filter:
    filtered = filtered[filtered["procuring_entity"].isin(buyer_filter)]

total_value = filtered["_value"].sum()
avg_participants = filtered["_participants"].mean()

st.metric("💰 Загальна сума контрактів", f"{total_value:,.2f} грн")
st.metric("👥 Середня кількість учасників", f"{avg_participants:.2f}")

st.subheader("📈 Сума контрактів за регіонами")
fig1 = px.bar(filtered.groupby("region")["_value"].sum().reset_index(),
              x="region", y="_value", title="Сума контрактів за регіонами", text_auto=True)
st.plotly_chart(fig1, use_container_width=True)

st.subheader("📊 Сума контрактів за категоріями")
fig2 = px.bar(filtered.groupby("category")["_value"].sum().reset_index(),
              x="category", y="_value", title="Сума контрактів за категоріями", text_auto=True)
st.plotly_chart(fig2, use_container_width=True)

st.download_button(
    label="⬇️ Завантажити результати (CSV)",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_prozorro.csv",
    mime="text/csv"
)
