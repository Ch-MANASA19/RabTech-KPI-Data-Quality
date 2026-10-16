
import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(
    page_title="Retail Business Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Retail Business Intelligence Dashboard")
st.caption("Interactive KPI dashboard | Synthetic retail practice data")

@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "clean_dataset.csv"
    if not file_path.exists():
        raise FileNotFoundError(
            "Please upload clean_dataset.csv to the repository root."
        )
    data = pd.read_csv(file_path)
    data["order_date"] = pd.to_datetime(
        data["order_date"], errors="coerce"
    )
    return data

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load dataset: {e}")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

if "order_date" in df.columns and df["order_date"].notna().any():
    min_date = df["order_date"].min().date()
    max_date = df["order_date"].max().date()
    date_range = st.sidebar.date_input(
        "Order date range", value=(min_date, max_date),
        min_value=min_date, max_value=max_date
    )
else:
    date_range = None

def filter_options(column, label):
    if column not in df.columns:
        return df
    options = sorted(df[column].dropna().astype(str).unique().tolist())
    selected = st.sidebar.multiselect(label, options, default=options)
    return selected

selected_categories = filter_options("category", "Category")
selected_segments = filter_options("customer_segment", "Customer segment")
selected_cities = filter_options("city", "City")
selected_statuses = filter_options("payment_status", "Payment status")

filtered = df.copy()

if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        filtered["order_date"].dt.date.between(start_date, end_date)
    ]

for col, values in [
    ("category", selected_categories),
    ("customer_segment", selected_segments),
    ("city", selected_cities),
    ("payment_status", selected_statuses)
]:
    if col in filtered.columns:
        filtered = filtered[
            filtered[col].astype(str).isin(values)
        ]

if filtered.empty:
    st.warning("No records match these filters. Change the filters.")
    st.stop()

# Executive KPI cards
revenue = filtered["net_sales"].sum() if "net_sales" in filtered else 0
orders = (
    filtered["order_id"].nunique()
    if "order_id" in filtered else len(filtered)
)
aov = revenue / orders if orders else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net Revenue", f"₹{revenue:,.2f}")
c2.metric("Orders", f"{orders:,}")
c3.metric("Average Order Value", f"₹{aov:,.2f}")
c4.metric("Customer Acquisition Cost", "N/A")

st.info(
    "Churn rate and customer acquisition cost cannot be calculated "
    "reliably because customer-level retention and marketing cost data "
    "are not available in this dataset."
)

# Revenue trend
st.subheader("Revenue Trend")
if "order_date" in filtered.columns:
    trend = (
        filtered.dropna(subset=["order_date"])
        .assign(month=lambda x: x["order_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["net_sales"].sum()
        .sort_values("month")
    )
    if not trend.empty:
        fig = px.area(
            trend, x="month", y="net_sales",
            markers=True, title="Monthly Net Revenue",
            labels={"month": "Month", "net_sales": "Net Revenue (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)

# Category analysis
left, right = st.columns(2)

with left:
    st.subheader("Revenue by Category")
    category_sales = (
        filtered.groupby("category", as_index=False)["net_sales"]
        .sum().sort_values("net_sales", ascending=False)
    )
    fig = px.bar(
        category_sales, x="category", y="net_sales",
        color="net_sales", title="Category Revenue",
        labels={"category": "Category", "net_sales": "Net Revenue (₹)"}
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Revenue by Customer Segment")
    segment_sales = (
        filtered.groupby("customer_segment", as_index=False)["net_sales"]
        .sum().sort_values("net_sales", ascending=False)
    )
    fig = px.bar(
        segment_sales, x="customer_segment", y="net_sales",
        color="customer_segment", title="Segment Revenue",
        labels={
            "customer_segment": "Customer Segment",
            "net_sales": "Net Revenue (₹)"
        }
    )
    st.plotly_chart(fig, use_container_width=True)

# Geographic visualization using city coordinates
st.subheader("Geographic Sales View")
city_coordinates = {
    "Hyderabad": (17.3850, 78.4867),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Pune": (18.5204, 73.8567),
    "Bengaluru": (12.9716, 77.5946),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639)
}

if "city" in filtered.columns:
    city_sales = filtered.groupby("city", as_index=False)["net_sales"].sum()
    city_sales["latitude"] = city_sales["city"].map(
        lambda x: city_coordinates.get(x, (None, None))[0]
    )
    city_sales["longitude"] = city_sales["city"].map(
        lambda x: city_coordinates.get(x, (None, None))[1]
    )
    mapped = city_sales.dropna(subset=["latitude", "longitude"])

    if not mapped.empty:
        fig = px.scatter_geo(
            mapped, lat="latitude", lon="longitude",
            size="net_sales", color="net_sales",
            hover_name="city", hover_data={"net_sales": ":,.2f"},
            scope="asia", title="City-wise Net Revenue",
            labels={"net_sales": "Net Revenue (₹)"}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "No city coordinates available for mapping. "
            "Use the city revenue table below."
        )
    st.dataframe(city_sales, use_container_width=True)

# Interactive detail table
st.subheader("Order Details")
display_cols = [
    c for c in [
        "order_id", "order_date", "city", "customer_segment",
        "category", "quantity", "discount_pct", "payment_status",
        "gross_sales", "net_sales"
    ] if c in filtered.columns
]
st.dataframe(filtered[display_cols], use_container_width=True)

st.download_button(
    "Download filtered data as CSV",
    data=filtered.to_csv(index=False).encode("utf-8"),
    file_name="filtered_retail_data.csv",
    mime="text/csv"
)

# PDF report export
def make_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Retail Business Dashboard Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Synthetic practice dataset; not real business results.",
                  styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Filtered records: {len(data):,}", styles["Normal"]),
        Paragraph(f"Net revenue: ₹{data['net_sales'].sum():,.2f}",
                  styles["Normal"]),
        Paragraph(f"Unique orders: {data['order_id'].nunique():,}",
                  styles["Normal"]),
        Paragraph(
            f"Average order value: ₹{data['net_sales'].sum() / max(data['order_id'].nunique(), 1):,.2f}",
            styles["Normal"]
        ),
        Spacer(1, 16),
        Paragraph("Revenue by Category", styles["Heading2"])
    ]

    summary = data.groupby("category", as_index=False)["net_sales"].sum()
    table_data = [["Category", "Net Revenue (₹)"]]
    for _, row in summary.iterrows():
        table_data.append([str(row["category"]), f"{row['net_sales']:,.2f}"])

    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT")
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()

st.subheader("Export Report")
try:
    pdf_bytes = make_pdf(filtered)
    st.download_button(
        "📄 Download Dashboard PDF",
        data=pdf_bytes,
        file_name="Dashboard_Report.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"PDF report could not be generated: {e}")

st.caption(
    "CAC and churn are unavailable without marketing spend and "
    "customer retention history. Dataset is synthetic practice data."
)
