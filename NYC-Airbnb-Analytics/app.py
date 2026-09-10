"""
Airbnb NYC — Interactive Analytics Dashboard
Run locally:  streamlit run app.py
Data file:    airbnb_nyc_cleaned.csv  (same folder as this script)
"""

import pandas as pd
import plotly.express as px
import streamlit as st


# Page config

st.set_page_config(
    page_title="Airbnb NYC Analytics",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSV_PATH = "NYC-Airbnb-Analytics/airbnb_nyc_cleaned.csv"



# Data loading

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Guard against extra whitespace in column names
    df.columns = [c.strip() for c in df.columns]
    return df


try:
    df = load_data(CSV_PATH)
except FileNotFoundError:
    st.error(
        f"Couldn't find `{CSV_PATH}`. Make sure the cleaned CSV is in the "
        "same folder as app.py (or update CSV_PATH at the top of the script)."
    )
    st.stop()

# Columns this dashboard expects to exist; extras are used opportunistically.
REQUIRED_COLS = {"neighbourhood_group", "neighbourhood", "room_type", "price"}
missing = REQUIRED_COLS - set(df.columns)
if missing:
    st.error(f"The CSV is missing required column(s): {', '.join(missing)}")
    st.stop()

HAS_LATLON = {"latitude", "longitude"}.issubset(df.columns)
HAS_VALUE_SCORE = "value_score" in df.columns
HAS_OCCUPANCY = "occupancy_pct" in df.columns
HAS_POWER_HOST = "is_power_host" in df.columns
HAS_REVIEWS = "number_of_reviews" in df.columns



# Sidebar — filters

st.sidebar.header("Filters")

boroughs = sorted(df["neighbourhood_group"].dropna().unique().tolist())
selected_boroughs = st.sidebar.multiselect(
    "Borough / Neighbourhood group", boroughs, default=boroughs
)

room_types = sorted(df["room_type"].dropna().unique().tolist())
selected_room_types = st.sidebar.multiselect(
    "Room type", room_types, default=room_types
)

price_min, price_max = int(df["price"].min()), int(df["price"].max())
selected_price = st.sidebar.slider(
    "Price range ($/night)",
    min_value=price_min,
    max_value=price_max,
    value=(price_min, min(price_max, 500)),  # sensible default, avoids outlier squash
)

if HAS_LATLON:
    show_map = st.sidebar.checkbox("Show map", value=True)
else:
    show_map = False

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data: Inside Airbnb (NYC), cleaned. Adjust filters above to update every "
    "chart and metric on the page."
)


# Apply filters

mask = (
    df["neighbourhood_group"].isin(selected_boroughs)
    & df["room_type"].isin(selected_room_types)
    & df["price"].between(selected_price[0], selected_price[1])
)
fdf = df[mask].copy()

# Header + KPIs

st.title("🏙️ Airbnb NYC — Analytics Dashboard")
st.caption(
    f"Showing **{len(fdf):,}** of {len(df):,} listings based on the filters selected."
)

if fdf.empty:
    st.warning("No listings match the current filters. Try widening your selection.")
    st.stop()

kpi_cols = st.columns(5 if (HAS_OCCUPANCY and HAS_REVIEWS) else 3)

kpi_cols[0].metric("Listings", f"{len(fdf):,}")
kpi_cols[1].metric("Avg. price / night", f"${fdf['price'].mean():,.0f}")
kpi_cols[2].metric("Median price / night", f"${fdf['price'].median():,.0f}")

col_idx = 3
if HAS_REVIEWS and col_idx < len(kpi_cols):
    kpi_cols[col_idx].metric("Avg. reviews / listing", f"{fdf['number_of_reviews'].mean():,.1f}")
    col_idx += 1
if HAS_OCCUPANCY and col_idx < len(kpi_cols):
    kpi_cols[col_idx].metric("Avg. occupancy", f"{fdf['occupancy_pct'].mean():,.1f}%")

st.markdown("---")


# Row 1 — Price distribution & Room type mix

c1, c2 = st.columns((2, 1))

with c1:
    st.subheader("Price distribution")
    fig_price = px.histogram(
        fdf,
        x="price",
        nbins=40,
        color="room_type",
        labels={"price": "Price ($/night)", "count": "Listings"},
        opacity=0.85,
    )
    fig_price.update_layout(
        bargap=0.05, legend_title_text="Room type", height=420
    )
    st.plotly_chart(fig_price, use_container_width=True)

with c2:
    st.subheader("Room type mix")
    room_counts = fdf["room_type"].value_counts().reset_index()
    room_counts.columns = ["room_type", "count"]
    fig_room = px.pie(
        room_counts, names="room_type", values="count", hole=0.45
    )
    fig_room.update_traces(textinfo="percent+label")
    fig_room.update_layout(height=420, showlegend=False)
    st.plotly_chart(fig_room, use_container_width=True)


# Row 2 — Neighbourhoods

st.subheader("Neighbourhoods")

n1, n2 = st.columns(2)

with n1:
    st.markdown("**Average price by borough**")
    borough_price = (
        fdf.groupby("neighbourhood_group")["price"]
        .mean()
        .round(0)
        .sort_values(ascending=False)
        .reset_index()
    )
    fig_borough = px.bar(
        borough_price,
        x="neighbourhood_group",
        y="price",
        labels={"neighbourhood_group": "Borough", "price": "Avg. price ($)"},
        text="price",
    )
    fig_borough.update_traces(texttemplate="$%{text}", textposition="outside")
    fig_borough.update_layout(height=400)
    st.plotly_chart(fig_borough, use_container_width=True)

with n2:
    st.markdown("**Top 15 neighbourhoods by listing count**")
    top_neigh = (
        fdf["neighbourhood"].value_counts().head(15).sort_values().reset_index()
    )
    top_neigh.columns = ["neighbourhood", "count"]
    fig_top = px.bar(
        top_neigh,
        x="count",
        y="neighbourhood",
        orientation="h",
        labels={"count": "Listings", "neighbourhood": ""},
    )
    fig_top.update_layout(height=400)
    st.plotly_chart(fig_top, use_container_width=True)


# Row 3 — Map (optional) + Value / Occupancy

if show_map and HAS_LATLON:
    st.subheader("Listings map")
    fig_map = px.scatter_map(
        fdf,
        lat="latitude",
        lon="longitude",
        color="price",
        size=fdf["price"].clip(upper=fdf["price"].quantile(0.95)),
        hover_name="name" if "name" in fdf.columns else None,
        hover_data={
            "neighbourhood": True,
            "room_type": True,
            "price": True,
            "latitude": False,
            "longitude": False,
        },
        color_continuous_scale="Viridis",
        zoom=9.5,
        height=550,
    )
    fig_map.update_layout(
        mapbox_style="carto-positron", margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_map, use_container_width=True)

if HAS_VALUE_SCORE or HAS_OCCUPANCY:
    st.subheader("Value & occupancy")
    v1, v2 = st.columns(2)

    if HAS_VALUE_SCORE:
        with v1:
            st.markdown("**Top 10 listings by value score**")
            cols_to_show = [
                c
                for c in ["name", "neighbourhood", "room_type", "price", "value_score"]
                if c in fdf.columns
            ]
            top_value = fdf.sort_values("value_score", ascending=False).head(10)[cols_to_show]
            st.dataframe(top_value, use_container_width=True, hide_index=True)

    if HAS_OCCUPANCY:
        with v2:
            st.markdown("**Occupancy vs. price**")
            fig_occ = px.scatter(
                fdf,
                x="price",
                y="occupancy_pct",
                color="room_type",
                opacity=0.6,
                labels={"price": "Price ($/night)", "occupancy_pct": "Occupancy (%)"},
            )
            fig_occ.update_layout(height=380)
            st.plotly_chart(fig_occ, use_container_width=True)


# Row 4 — Power hosts (if available)

if HAS_POWER_HOST:
    st.subheader("Power hosts vs. other hosts")
    p1, p2 = st.columns(2)

    with p1:
        ph_price = fdf.groupby("is_power_host")["price"].mean().round(0).reset_index()
        fig_ph = px.bar(
            ph_price,
            x="is_power_host",
            y="price",
            labels={"is_power_host": "Power host", "price": "Avg. price ($)"},
            text="price",
        )
        fig_ph.update_traces(texttemplate="$%{text}", textposition="outside")
        fig_ph.update_layout(height=360)
        st.plotly_chart(fig_ph, use_container_width=True)

    with p2:
        ph_counts = fdf["is_power_host"].value_counts().reset_index()
        ph_counts.columns = ["is_power_host", "count"]
        fig_ph_count = px.pie(
            ph_counts, names="is_power_host", values="count", hole=0.45
        )
        fig_ph_count.update_layout(height=360)
        st.plotly_chart(fig_ph_count, use_container_width=True)


# Raw data explorer

with st.expander("🔍 View filtered raw data"):
    st.dataframe(fdf, use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered data as CSV",
        data=fdf.to_csv(index=False).encode("utf-8"),
        file_name="airbnb_filtered.csv",
        mime="text/csv",
    )

st.markdown("---")
st.caption("Built with Streamlit · Data source: Inside Airbnb (NYC)")
