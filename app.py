import pandas as pd
from PIL import Image
import streamlit as st
import plotly.express as px

# Set default template and color scale for Plotly
px.defaults.template = 'plotly_dark'
px.defaults.color_continuous_scale = 'plasma'

# Custom CSS styling for a modern and attractive theme
st.markdown(
    """
    <style>
    /* Main header styling */
    .main-header {
        font-size: 36px;
        color: #FFD700; /* Gold color */
        text-align: center;
        font-weight: bold;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px #000000;
    }
    /* Sub-header styling */
    .sub-header {
        font-size: 24px;
        color: #87CEEB; /* Sky blue color */
        font-weight: bold;
        margin-top: 20px;
    }
    /* Sidebar styling */
    .st-sidebar {
        background-color: #1E1E1E; /* Dark background */
        color: #FFD700; /* Gold text */
    }
    .st-sidebar h1, h2, h3, h4, h5, h6 {
        color: #FFD700;
    }
    /* General text styling */
    .stMarkdown {
        color: #FFFFFF; /* White text */
    }
    /* Button styling */
    .stButton>button {
        background-color: #FFD700;
        color: #000000;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cache data loading for better performance
@st.cache_data
def load_data(file_path, is_prediction=False):
    data = pd.read_csv(file_path)
    data['Bulan'] = pd.to_datetime(data['Bulan'], errors='coerce')
    data = data[data['Bulan'].notnull()]
    if is_prediction:
        data.rename(columns={'Total Penjualan': 'Prediksi Total Penjualan'}, inplace=True)
    return data

# Header
st.markdown("<div class='main-header'>📊 Dashboard Analisis Penjualan</div>", unsafe_allow_html=True)

# Load and display the logo in the sidebar
img = Image.open('logo.png')
st.sidebar.image(img, use_container_width=True)

# Sidebar: Select Dataset
st.sidebar.header("📂 Pilih Dataset")
dataset_option = st.sidebar.radio(
    "Pilih dataset untuk analisis:",
    options=["Data Prediksi", "Data Sebelum Prediksi", "Perbandingan"]
)

# Load datasets
data_prediksi = load_data('Data_Prediction.csv', is_prediction=True)
data_sebelum = load_data('Data_Before_Prediction.csv', is_prediction=False)

# Add columns to distinguish data types
data_prediksi['Jenis Data'] = 'Prediksi'
data_sebelum['Jenis Data'] = 'Sebelum Prediksi'

# Combine datasets for comparison
combined_data = pd.concat([data_prediksi, data_sebelum])
combined_data['Total Penjualan Gabungan'] = combined_data['Prediksi Total Penjualan'].combine_first(combined_data['Total Penjualan'])
combined_data['Total Penjualan Gabungan'] = combined_data['Total Penjualan Gabungan'].fillna(0)
combined_data['Total Penjualan Gabungan'] = pd.to_numeric(combined_data['Total Penjualan Gabungan'], errors='coerce')

# Sidebar: Filter Data
st.sidebar.header("🔍 Filter Data")
combined_data['Bulan'] = combined_data['Bulan'].dt.to_period('M').astype(str)
unique_months = combined_data['Bulan'].unique()
selected_month = st.sidebar.selectbox("Pilih Bulan", options=['Semua'] + list(unique_months), index=0)

unique_categories = combined_data['Kategori Produk'].unique()
selected_category = st.sidebar.selectbox("Pilih Kategori Produk", options=['Semua'] + list(unique_categories), index=0)

filtered_data = combined_data.copy()
if selected_month != 'Semua':
    filtered_data = filtered_data[filtered_data['Bulan'] == selected_month]
if selected_category != 'Semua':
    filtered_data = filtered_data[filtered_data['Kategori Produk'] == selected_category]

# Display filtered data
st.markdown(f"<div class='sub-header'>📁 Dataset yang dipilih: {dataset_option}</div>", unsafe_allow_html=True)
if filtered_data.empty:
    st.error("❌ Tidak ada data untuk filter yang dipilih.")
else:
    # Visualize data based on selection
    if dataset_option == "Data Prediksi":
        y_axis_label = 'Prediksi Total Penjualan'
        st.subheader('📈 Analisis Data Prediksi')
    elif dataset_option == "Data Sebelum Prediksi":
        y_axis_label = 'Total Penjualan'
        st.subheader('📉 Analisis Data Sebelum Prediksi')
    else:
        y_axis_label = 'Total Penjualan Gabungan'
        st.subheader('🔄 Perbandingan Data Prediksi dan Sebelum Prediksi')

    # Monthly Sales Trend
    st.markdown("<div class='sub-header'>📅 Tren Penjualan Bulanan</div>", unsafe_allow_html=True)
    monthly_sales = filtered_data.groupby(['Bulan', 'Jenis Data'])[y_axis_label].sum().reset_index()
    monthly_sales = monthly_sales.sort_values(by='Bulan')
    fig1 = px.line(
        monthly_sales,
        x='Bulan',
        y=y_axis_label,
        color='Jenis Data' if dataset_option == "Perbandingan" else None,
        labels={'Bulan': 'Bulan', y_axis_label: f'{y_axis_label} (dalam unit)'},
        title="Tren Penjualan Bulanan"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Sales Distribution by Category
    st.markdown("<div class='sub-header'>📦 Distribusi Penjualan Berdasarkan Kategori Produk</div>", unsafe_allow_html=True)
    category_sales = filtered_data.groupby(['Kategori Produk', 'Jenis Data'])[y_axis_label].sum().reset_index()
    fig2 = px.bar(
        category_sales,
        x='Kategori Produk',
        y=y_axis_label,
        color='Jenis Data' if dataset_option == "Perbandingan" else None,
        barmode='group' if dataset_option == "Perbandingan" else None,
        labels={'Kategori Produk': 'Kategori Produk', y_axis_label: f'{y_axis_label} (dalam unit)'},
        title="Distribusi Penjualan Berdasarkan Kategori Produk"
    )
    st.plotly_chart(fig2, use_container_width=True)

    # Top Products
    st.markdown("<div class='sub-header'>🏆 Produk dengan Penjualan Tertinggi</div>", unsafe_allow_html=True)
    top_products = (
        filtered_data.groupby(['Suku Cadang', 'Jenis Data'])[y_axis_label]
        .sum()
        .reset_index()
        .nlargest(10, y_axis_label)
    )
    fig3 = px.bar(
        top_products,
        x='Suku Cadang',
        y=y_axis_label,
        color='Jenis Data' if dataset_option == "Perbandingan" else None,
        labels={'Suku Cadang': 'Suku Cadang', y_axis_label: f'{y_axis_label} (dalam unit)'},
        title="10 Produk dengan Penjualan Tertinggi"
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Comparison Chart
    if dataset_option == "Perbandingan":
        st.markdown("<div class='sub-header'>📊 Perbandingan Total Penjualan Berdasarkan Bulan</div>", unsafe_allow_html=True)
        comparison_data = filtered_data.groupby(['Bulan', 'Jenis Data'])['Total Penjualan Gabungan'].sum().reset_index()
        fig_comparison = px.bar(
            comparison_data,
            x='Bulan',
            y='Total Penjualan Gabungan',
            color='Jenis Data',
            barmode='group',
            labels={'Total Penjualan Gabungan': 'Total Penjualan (dalam unit)', 'Bulan': 'Bulan'},
            title='Perbandingan Total Penjualan Sebelum dan Setelah Prediksi'
        )
        st.plotly_chart(fig_comparison, use_container_width=True)