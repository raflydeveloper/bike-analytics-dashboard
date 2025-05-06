import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

# Set tema seaborn
sns.set_theme(style='dark')

# Load dataset
file_path = r"\Data_Analyst_Bike\Dashboard\all_data.csv"
all_df = pd.read_csv(file_path)

# Konversi dan urutkan tanggal
all_df["dteday"] = pd.to_datetime(all_df["dteday"])
all_df.sort_values(by="dteday", inplace=True)
all_df.reset_index(drop=True, inplace=True)

# Konversi kolom kategorikal
categorical_columns = ["season", "yr", "mnth", "holiday", "weekday", "workingday"]
for column in categorical_columns:
    all_df[column] = all_df[column].astype("category")

# Rentang tanggal untuk filter
min_date = all_df["dteday"].min()
max_date = all_df["dteday"].max()

# Sidebar
with st.sidebar:
    st.title("Filter Data")
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date, max_value=max_date,
        value=[min_date, max_date]
    )

# Filter data utama
main_df = all_df[(all_df["dteday"] >= pd.to_datetime(start_date)) & 
                 (all_df["dteday"] <= pd.to_datetime(end_date))]

# Mapping nama kategori
season_mapping = {
    1: "Spring",
    2: "Summer",
    3: "Fall",
    4: "Winter"
}
weekday_mapping = {
    0: "Sunday",
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday"
}
month_mapping = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}

main_df["season"] = main_df["season"].cat.codes + 1
main_df["season"] = main_df["season"].map(season_mapping)

main_df["weekday"] = main_df["weekday"].cat.codes
main_df["weekday"] = main_df["weekday"].map(weekday_mapping)

main_df["mnth"] = main_df["mnth"].cat.codes + 1
main_df["mnth"] = main_df["mnth"].map(month_mapping)

# =====================
# Fungsi & Visualisasi
# =====================

st.header('Visual Data Peminjaman Sepeda 2011 - 2012')

# --- DAILY RENTALS ---
st.subheader('Daily Bike Rentals')
daily_rentals = main_df.groupby("dteday")["cnt"].sum().reset_index()
daily_rentals.rename(columns={"dteday": "rental_date", "cnt": "rental_count"}, inplace=True)

col1, col2 = st.columns(2)

with col1:
    total_rentals = daily_rentals.rental_count.sum()
    st.metric("Total Rentals", value=total_rentals)

with col2:
    total_revenue = format_currency(total_rentals * 5, "AUD", locale='es_CO')
    st.metric("Estimated Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(daily_rentals["rental_date"], daily_rentals["rental_count"], marker='o', linewidth=2, color="#90CAF9")
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

# --- RENTAL BY SEASON ---
st.subheader("Customer Demographics by Season")
season_counts = main_df["season"].value_counts().reset_index()
season_counts.columns = ["season", "customer_count"]

fig, ax = plt.subplots(figsize=(20, 10))
sns.barplot(x="season", y="customer_count", data=season_counts, palette="Blues", ax=ax)
ax.set_title("Number of Rentals by Season", fontsize=30)
st.pyplot(fig)

# --- RFM ANALYSIS SIMULASI ---
def create_rfm_df(df):
    df = df.copy()
    df["user_id"] = df["instant"] % 100  # Simulasi user_id
    df["rental_date"] = df["dteday"]

    rfm = df.groupby("user_id").agg({
        "rental_date": "max",
        "instant": "count",
        "cnt": "sum"
    }).reset_index()

    rfm.columns = ["customer_id", "max_rental_date", "frequency", "monetary"]
    recent_date = df["rental_date"].max()
    rfm["recency"] = (recent_date - rfm["max_rental_date"]).dt.days
    rfm.drop("max_rental_date", axis=1, inplace=True)
    return rfm

rfm_df = create_rfm_df(main_df)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Average Recency (days)", value=round(rfm_df["recency"].mean(), 1))

with col2:
    st.metric("Average Frequency", value=round(rfm_df["frequency"].mean(), 2))

with col3:
    st.metric("Average Monetary", value=format_currency(rfm_df["monetary"].mean(), "AUD", locale='es_CO'))

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9"] * 5

sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency").head(5), palette=colors, ax=ax[0])
ax[0].set_title("By Recency", fontsize=30)

sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_title("By Frequency", fontsize=30)

sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_title("By Monetary", fontsize=30)

st.pyplot(fig)

# Footer
st.caption("Copyright (c) Rafly 2025")
