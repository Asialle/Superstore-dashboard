import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# Globális matplotlib beállítások, hogy a feliratok mindig látszódjanak
plt.rcParams.update({
    "text.color": "black",
    "axes.labelcolor": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "axes.titlecolor": "black"
})


# Adatok

data = pd.read_csv("data.csv")


data["Order Date"] = pd.to_datetime(data["Order Date"], dayfirst=True)
data["Ship Date"] = pd.to_datetime(data["Ship Date"], dayfirst=True)

# Új oszlop: év és hónap
data["Year"] = data["Order Date"].dt.year.astype('Int64')
data["Month"] = data["Order Date"].dt.month.astype('Int64')

# Új oszlop: szállítási napok
data["Days_to_Ship"] = (data["Order Date"] - data["Ship Date"]).dt.days


#  Streamlit dashboard beállítás

st.set_page_config(page_title="Superstore Dashboard", layout="wide")

# háttérszín és KPI dobozok
st.markdown(
    """
    <style>
    .stApp { background-color: #f7f9fb; font-family: 'Segoe UI', sans-serif; }
    .metric-container { background-color: #0058a3; border-radius: 12px; padding: 15px; text-align: center; margin-bottom:10px; color:white;}
    .metric-container h2 { margin: 0; font-size: 1.6rem; }
    .metric-container h3 { margin: 0; font-size: 1.1rem; color: #ffcc00; }
    </style>
    """, unsafe_allow_html=True
)

st.title("Superstore Sales Dashboard")


#  Oldalsáv szűrők
possible_years = sorted(data["Year"].dropna().unique())
year_filter = st.sidebar.selectbox("Select year:", options=["All"] + [int(y) for y in possible_years], index=0)

possible_months = sorted(data["Month"].dropna().unique())
month_filter = st.sidebar.selectbox("Select month:", options=["All"] + [int(m) for m in possible_months], index=0)

regions = sorted(data["Region"].dropna().unique())
region_options = ["All"] + regions
region_filter = st.sidebar.multiselect("Select Region:", options=region_options, default=["All"])

categories = sorted(data["Category"].dropna().unique())
category_options = ["All"] + categories
category_filter = st.sidebar.multiselect("Select Category:", options=category_options, default=["All"])

segments = sorted(data["Segment"].dropna().unique())
segment_options = ["All"] + segments
segment_filter = st.sidebar.multiselect("Select Segment:", options=segment_options, default=["All"])

#  Adatok szűrése
df = data.copy()
if year_filter != "All":
    df = df[df["Year"] == year_filter]
if month_filter != "All":
    df = df[df["Month"] == month_filter]
if "All" not in region_filter:
    df = df[df["Region"].isin(region_filter)]
if "All" not in category_filter:
    df = df[df["Category"].isin(category_filter)]
if "All" not in segment_filter:
    df = df[df["Segment"].isin(segment_filter)]

# színpaletta
palette = {
    "Sales": "#ffcc00",
    "Profit": "#0058a3",
    "Orders": "#ffcc00",
    "Loss": "#e57373",
    "Shipping": "#0058a3",
    "Furniture": "#0058a3",
    "Office Supplies": "#ffcc00",
    "Technology": "#0058a3"
}

# KPI-ok színes dobozokkal és mini-sparkline-al
col1, col2, col3 = st.columns(3)

def plot_sparkline(series, color="#0058a3"):
    fig, ax = plt.subplots(figsize=(2,0.5))
    ax.plot(series, color=color, linewidth=1)
    ax.axis('off')
    st.pyplot(fig)

with col1:
    total_sales = df["Sales"].sum()
    st.markdown(f'<div class="metric-container"><h3>Total Sales</h3><h2>${total_sales/1e6:.1f}M</h2></div>', unsafe_allow_html=True)
    sales_series = df.groupby("Order Date")["Sales"].sum()
    plot_sparkline(sales_series, color=palette["Sales"])

with col2:
    total_profit = df["Profit"].sum()
    st.markdown(f'<div class="metric-container"><h3>Total Profit</h3><h2>${total_profit/1e3:.1f}k</h2></div>', unsafe_allow_html=True)
    profit_series = df.groupby("Order Date")["Profit"].sum()
    plot_sparkline(profit_series, color=palette["Profit"])

with col3:
    total_orders = df["Order ID"].nunique()
    st.markdown(f'<div class="metric-container"><h3>Number of Orders</h3><h2>{total_orders}</h2></div>', unsafe_allow_html=True)
    orders_series = df.groupby("Order Date")["Order ID"].nunique()
    plot_sparkline(orders_series, color=palette["Orders"])

# Top 10 Products by Sales
st.subheader("🔝 Top 10 Products by Sales")
top_sales = df.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(10).reset_index()

# Skálázás ezresben, hogy a szám rövidebb legyen
top_sales["Sales_k"] = top_sales["Sales"] / 1000

fig, ax = plt.subplots(figsize=(14, 8))
bars = ax.barh(top_sales["Product Name"], top_sales["Sales_k"], color=palette["Sales"])
ax.set_xlabel("Sales (k$)")
ax.set_ylabel("Product Name")
ax.set_title("Top 10 Products by Sales")
plt.gca().invert_yaxis()

# számok a sávon belül, max 95%
for bar, value in zip(bars, top_sales["Sales_k"]):
    text_x = value * 0.95
    ax.text(text_x, bar.get_y() + bar.get_height()/2,
            f'{value:.2f}', ha='right', va='center', color='white', fontsize=10)

st.pyplot(fig, use_container_width=False)



#  Top 10 Products by Profit
st.subheader("💰 Top 10 Products by Profit")
top_profit = df.groupby("Product Name")["Profit"].sum().sort_values(ascending=False).head(10).reset_index()
fig, ax = plt.subplots()
ax.barh(top_profit["Product Name"], top_profit["Profit"], color=palette["Profit"])
ax.set_xlabel("Profit ($)")
ax.set_ylabel("Product Name")
ax.set_title("Top 10 Products by Profit")
plt.gca().invert_yaxis()
for i, v in enumerate(top_profit["Profit"]):
    ax.text(v + 0.01*v, i, f"{v:.2f}")
st.pyplot(fig)

# 📌 Worst 5 Products by Loss
st.subheader("💔 Worst 5 Products by Loss")
worst_loss = df.groupby("Product Name")["Profit"].sum().sort_values().head(5).reset_index()
fig, ax = plt.subplots()
ax.barh(worst_loss["Product Name"], worst_loss["Profit"], color=palette["Loss"])
ax.set_xlabel("Profit ($)")
ax.set_ylabel("Product Name")
ax.set_title("Worst 5 Products by Profit")
plt.gca().invert_yaxis()
for i, v in enumerate(worst_loss["Profit"]):
    ax.text(v - 0.01*abs(v), i, f"{v:.2f}")
st.pyplot(fig)

#  Átlagos szállítási idő

st.subheader("🚚 Average Shipping Time (days)")
avg_ship = df["Days_to_Ship"].mean()
min_ship = df["Days_to_Ship"].min()
max_ship = df["Days_to_Ship"].max()
fig, ax = plt.subplots()
ax.bar(["Average Days to Ship"], [avg_ship], color=palette["Shipping"])
ax.set_ylim(min_ship, max_ship)
ax.set_ylabel("Days")
ax.set_title("Average Shipping Time")
st.pyplot(fig)


#  Éves eladási trendek kategóriák szerint

st.subheader("📈 Yearly Sales Trends by Category")
sales_trend = df.groupby(["Year", "Category"])["Sales"].sum().reset_index()
fig, ax = plt.subplots()
categories = sales_trend["Category"].unique()
years = sales_trend["Year"].unique()
bottom = np.zeros(len(years))
for category in categories:
    subset = sales_trend[sales_trend["Category"] == category]
    ax.bar(subset["Year"], subset["Sales"], label=category, bottom=bottom, color=palette[category])
    bottom += subset["Sales"].values
ax.set_xlabel("Year")
ax.set_ylabel("Sales ($)")
ax.set_title("Yearly Sales by Category")
ax.legend()
st.pyplot(fig)


#  Heatmap kategóriák szerint
st.subheader("🔥 Correlation Heatmap of Sales & Profit")
corr_df = df[["Sales","Profit","Quantity","Discount","Days_to_Ship"]].corr()
fig, ax = plt.subplots()
cax = ax.matshow(corr_df, cmap="YlGnBu")
plt.xticks(range(len(corr_df.columns)), corr_df.columns, rotation=45)
plt.yticks(range(len(corr_df.columns)), corr_df.columns)
plt.colorbar(cax)
st.pyplot(fig)
