import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Global Market Pulse", layout="wide", page_icon="📊")

# ---------------------------------------------------------------------------
# DARK TERMINAL THEME
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e2e8f0; }
    h1, h2, h3 { color: #f1f5f9 !important; font-family: 'Segoe UI', sans-serif; }
    .sub-header { color: #64748b; font-size: 0.95rem; margin-top: -10px; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131a27, #0f1117);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    div[data-testid="stMetricValue"] { color: #f1f5f9 !important; }

    /* Section dividers */
    hr { border-color: #1e293b; }

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #facc15 !important; }

    /* Dataframe */
    div[data-testid="stDataFrame"] { border: 1px solid #1e293b; border-radius: 10px; }

    /* Insight cards */
    .insight-card {
        background: #131a27; border: 1px solid #1e293b; border-radius: 10px;
        padding: 14px 16px; margin-bottom: 10px; font-size: 0.92rem; color: #cbd5e1;
    }
    .insight-tag {
        display:inline-block; padding:2px 8px; border-radius:6px; font-size:0.75rem;
        font-weight:700; margin-right:8px;
    }
    .tag-pos { background:#16302180; color:#4ade80; }
    .tag-neg { background:#3f1d1d80; color:#f87171; }
    .tag-neu { background:#1e293b; color:#facc15; }

    .ticker-strip {
        white-space: nowrap; overflow: hidden; background:#131a27;
        border:1px solid #1e293b; border-radius:8px; padding:8px 0; margin-bottom:18px;
    }
    .ticker-item { display:inline-block; padding:0 24px; font-size:0.9rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Global Market Pulse")
st.markdown('<p class="sub-header">Live snapshot across indices, currencies, metals, energy & crypto — with returns, heatmaps and quick takeaways.</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ASSET UNIVERSE (grouped)
# ---------------------------------------------------------------------------
GROUPS = {
    "Equity Indices": {
        "Nifty 50": "^NSEI",
        "Nifty Bank": "^NSEBANK",
        "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC",
        "Nikkei 225": "^N225",
        "Hang Seng": "^HSI",
        "KOSPI": "^KS11",
        "Karachi 100": "^KSE",
    },
    "Currencies": {
        "USD-INR": "INR=X",
    },
    "Commodities": {
        "Gold": "GC=F",
        "Silver": "SI=F",
        "Crude Oil": "CL=F",
    },
    "Crypto": {
        "Bitcoin": "BTC-USD",
        "Ethereum": "ETH-USD",
        "Dogecoin": "DOGE-USD",
    },
}

ASSETS = {name: tkr for grp in GROUPS.values() for name, tkr in grp.items()}
TICKER_TO_NAME = {v: k for k, v in ASSETS.items()}
NAME_TO_GROUP = {name: grp for grp, items in GROUPS.items() for name in items}

PERIODS = [
    ("Last Day", 1),
    ("1 Week", 7),
    ("1 Month", 30),
    ("3 Month", 91),
    ("1 Year", 365),
    ("2 Year", 2 * 365),
    ("3 Year", 3 * 365),
    ("5 Year", 5 * 365),
    ("10 Year", 10 * 365),
]

# ---------------------------------------------------------------------------
# DATA FETCH
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_market_data():
    table_rows, returns_matrix, history = [], {}, {}

    for name, ticker in ASSETS.items():
        data = yf.download(ticker, start=datetime.now() - timedelta(days=11 * 365),
                            end=datetime.now(), progress=False)
        if data.empty:
            continue

        close = data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        close = pd.to_numeric(close, errors="coerce").dropna()
        if len(close) < 2:
            continue

        current_price = float(close.iloc[-1])
        history[name] = close

        def calc_return(days_ago):
            try:
                if days_ago == 1:
                    past_price = float(close.iloc[-2])
                else:
                    target_date = close.index[-1] - pd.Timedelta(days=days_ago)
                    past_price = float(close.loc[:target_date].iloc[-1])
                return ((current_price - past_price) / past_price) * 100
            except Exception:
                return np.nan

        row = {"Asset": name, "Group": NAME_TO_GROUP[name], "Latest Price": current_price}
        rmat = {}
        for label, days in PERIODS:
            val = calc_return(days)
            row[label] = val
            rmat[label] = val
        table_rows.append(row)
        returns_matrix[name] = rmat

    df = pd.DataFrame(table_rows)
    ret_df = pd.DataFrame(returns_matrix).T
    return df, ret_df, history


with st.spinner("Fetching live market data..."):
    df, ret_df, history = get_market_data()

period_labels = [p[0] for p in PERIODS]

# ---------------------------------------------------------------------------
# TICKER STRIP — quick glance row
# ---------------------------------------------------------------------------
strip_items = ""
for _, row in df.iterrows():
    val = row["Last Day"]
    color = "#4ade80" if val >= 0 else "#f87171"
    arrow = "▲" if val >= 0 else "▼"
    strip_items += (f'<span class="ticker-item">{row["Asset"]}: '
                     f'<span style="color:{color}">{arrow} {val:+.2f}%</span></span>')
st.markdown(f'<div class="ticker-strip">{strip_items}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# HERO METRICS
# ---------------------------------------------------------------------------
st.subheader("Headline Movers")
hero_assets = ["Nifty 50", "Nasdaq", "S&P 500", "Gold", "Bitcoin", "USD-INR"]
cols = st.columns(len(hero_assets))
for c, asset in zip(cols, hero_assets):
    if asset in df["Asset"].values:
        r = df[df["Asset"] == asset].iloc[0]
        c.metric(asset, f"{r['Latest Price']:,.2f}", f"{r['Last Day']:+.2f}%")

st.divider()

# ---------------------------------------------------------------------------
# AUTO-GENERATED INSIGHTS
# ---------------------------------------------------------------------------
st.subheader("🧠 Quick Insights")

insights = []

# Best / worst 1-day performers
day = df.dropna(subset=["Last Day"])
if not day.empty:
    best = day.loc[day["Last Day"].idxmax()]
    worst = day.loc[day["Last Day"].idxmin()]
    insights.append(("pos", f"<b>{best['Asset']}</b> is today's top mover, up <b>{best['Last Day']:+.2f}%</b>."))
    insights.append(("neg", f"<b>{worst['Asset']}</b> is lagging today, down <b>{worst['Last Day']:+.2f}%</b>."))

# Best / worst 1-year performers
yr = df.dropna(subset=["1 Year"])
if not yr.empty:
    best_y = yr.loc[yr["1 Year"].idxmax()]
    worst_y = yr.loc[yr["1 Year"].idxmin()]
    insights.append(("pos", f"Over the past year, <b>{best_y['Asset']}</b> leads the pack with <b>{best_y['1 Year']:+.2f}%</b>."))
    insights.append(("neg", f"<b>{worst_y['Asset']}</b> is the weakest 1-year performer at <b>{worst_y['1 Year']:+.2f}%</b>."))

# Gold vs equities (risk sentiment)
if "Gold" in df["Asset"].values and "Nasdaq" in df["Asset"].values:
    gold_1m = df.loc[df["Asset"] == "Gold", "1 Month"].iloc[0]
    nasdaq_1m = df.loc[df["Asset"] == "Nasdaq", "1 Month"].iloc[0]
    if gold_1m > nasdaq_1m:
        insights.append(("neu", f"Gold (<b>{gold_1m:+.2f}%</b>) is outpacing Nasdaq (<b>{nasdaq_1m:+.2f}%</b>) over the last month — a hint of risk-off positioning."))
    else:
        insights.append(("neu", f"Nasdaq (<b>{nasdaq_1m:+.2f}%</b>) is outpacing Gold (<b>{gold_1m:+.2f}%</b>) over the last month — risk-on tone in markets."))

# Crypto volatility check
crypto_names = list(GROUPS["Crypto"].keys())
crypto_present = [c for c in crypto_names if c in df["Asset"].values]
if crypto_present:
    crypto_1m = df[df["Asset"].isin(crypto_present)][["Asset", "1 Month"]].dropna()
    if not crypto_1m.empty:
        top_crypto = crypto_1m.loc[crypto_1m["1 Month"].idxmax()]
        insights.append(("neu", f"In crypto, <b>{top_crypto['Asset']}</b> has the strongest 1-month move at <b>{top_crypto['1 Month']:+.2f}%</b>."))

# INR move
if "USD-INR" in df["Asset"].values:
    inr_1m = df.loc[df["Asset"] == "USD-INR", "1 Month"].iloc[0]
    direction = "weakened" if inr_1m > 0 else "strengthened"
    insights.append(("neu", f"The Rupee has {direction} <b>{abs(inr_1m):.2f}%</b> against the USD over the past month."))

for tag, text in insights:
    cls = {"pos": "tag-pos", "neg": "tag-neg", "neu": "tag-neu"}[tag]
    label = {"pos": "UP", "neg": "DOWN", "neu": "WATCH"}[tag]
    st.markdown(f'<div class="insight-card"><span class="insight-tag {cls}">{label}</span>{text}</div>', unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# RETURNS HEATMAP
# ---------------------------------------------------------------------------
st.subheader("🔥 Returns Heatmap")
st.caption("Performance across timeframes — green is positive, red is negative.")

heat_df = ret_df[period_labels].copy()
heat_df = heat_df.loc[df["Asset"]]  # preserve group order
heat_values = heat_df.to_numpy(dtype=float)
finite_heat = np.abs(heat_values[np.isfinite(heat_values)])
heat_limit = max(5.0, float(np.nanpercentile(finite_heat, 90))) if finite_heat.size else 5.0

fig_heat = go.Figure(data=go.Heatmap(
    z=heat_values,
    x=heat_df.columns,
    y=heat_df.index,
    colorscale=[
        [0.00, "#ff3333"],  # Bright Red for deep negative
        [0.45, "#4a1212"],  # Dark Red for slight negative
        [0.50, "#0f1117"],  # App Background Color for exactly zero
        [0.55, "#123d24"],  # Dark Green for slight positive
        [1.00, "#00cc96"],  # Bright Green for deep positive
    ],
    zmin=-heat_limit,
    zmax=heat_limit,
    zmid=0,
    text=np.round(heat_values, 2),
    texttemplate="%{text:+.2f}%",
    textfont={"size": 11, "color": "#ffffff"},
    hovertemplate="%{y}<br>%{x}: %{z:+.2f}%<extra></extra>",
    colorbar=dict(title="Return %"),
))

fig_heat.update_layout(
    plot_bgcolor="#0b0e14", paper_bgcolor="#0b0e14",
    font=dict(color="#e2e8f0"),
    height=600, margin=dict(l=10, r=10, t=10, b=10),
)

# Reverse the Y-axis to put the first asset (Nifty 50) at the top
fig_heat.update_yaxes(autorange="reversed")

# Move the X-axis labels to the top
fig_heat.update_xaxes(side="top")

st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# BAR CHART — 1 YEAR RETURNS BY GROUP
# ---------------------------------------------------------------------------
st.subheader("📈 1-Year Performance by Asset Class")

bar_df = df.dropna(subset=["1 Year"]).sort_values("1 Year", ascending=True)
bar_values = bar_df["1 Year"].astype(float)

# Calculate extra padding so large percentage text doesn't get cut off
bar_span = max(float(bar_values.max() - bar_values.min()), 1.0)
bar_padding = max(bar_span * 0.18, 10.0) 
bar_min = min(float(bar_values.min()), 0.0) - bar_padding
bar_max = max(float(bar_values.max()), 0.0) + bar_padding

fig_bar = px.bar(
    bar_df, x="1 Year", y="Asset", color="Group", orientation="h",
    text=bar_values.map(lambda v: f"<b>{v:+.2f}%</b>"), # Bold text formatting
    # Using brighter, distinct colors for the categories
    color_discrete_sequence=["#00cc96", "#ff9933", "#636efa", "#ef553b"] 
)

fig_bar.update_traces(
    textposition="outside",
    textfont=dict(size=14, color="#ffffff"), # Bright white, legible text
    cliponaxis=False,
)

fig_bar.update_layout(
    plot_bgcolor="#0b0e14", paper_bgcolor="#0b0e14",
    font=dict(color="#e2e8f0"),
    height=750,  # Increased height to give the bars room to breathe
    xaxis_title="1-Year Return (%)", yaxis_title="",
    
    # Moved the legend to the top right to save vertical space
    legend=dict(
        title="", orientation="h", 
        yanchor="bottom", y=1.02, xanchor="right", x=1
    ),
    margin=dict(l=10, r=80, t=40, b=20),
)

# Make the asset names on the left slightly larger
fig_bar.update_yaxes(tickfont=dict(size=13)) 

# Remove vertical grid lines for a cleaner, modern look
fig_bar.update_xaxes(
    range=[bar_min, bar_max], 
    zeroline=True, zerolinecolor="#64748b", 
    showgrid=False 
)

st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# PRICE TREND EXPLORER (sparklines + detail chart)
# ---------------------------------------------------------------------------
st.subheader("📉 Price Trends")

tab_names = list(GROUPS.keys())
tabs = st.tabs(tab_names)

for tab, group_name in zip(tabs, tab_names):
    with tab:
        group_assets = [a for a in GROUPS[group_name].keys() if a in history]
        n = len(group_assets)
        ncols = min(4, n) if n else 1
        cols = st.columns(ncols)
        for i, asset in enumerate(group_assets):
            series = pd.to_numeric(history[asset], errors="coerce").dropna().tail(180)
            change = ret_df.loc[asset, "1 Month"]
            line_color = "#4ade80" if pd.notna(change) and change >= 0 else "#f87171"
            change_label = f"{change:+.2f}%" if pd.notna(change) else "N/A"
            spark = go.Figure(go.Scatter(
                x=series.index, y=series.to_numpy(dtype=float), mode="lines",
                line=dict(color=line_color, width=2), fill="tozeroy",
                fillcolor="rgba(74, 222, 128, 0.12)" if line_color == "#4ade80"
                          else "rgba(248, 113, 113, 0.12)",
                hovertemplate="%{x|%d %b %Y}<br>%{y:,.2f}<extra></extra>",
            ))
            spark.update_layout(
                height=130, margin=dict(l=0, r=0, t=28, b=0),
                paper_bgcolor="#131a27", plot_bgcolor="#131a27",
                title=dict(text=f"{asset}  ·  1M {change_label}", font=dict(size=12, color="#e2e8f0")),
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                showlegend=False,
            )
            cols[i % ncols].plotly_chart(spark, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# FULL DATA TABLE
# ---------------------------------------------------------------------------
st.subheader("📋 Full Performance Table")

display_df = df.set_index("Asset")[["Group", "Latest Price"] + period_labels].copy()
display_df["Latest Price"] = display_df["Latest Price"].map(lambda v: f"{v:,.2f}")

def style_returns(val):
    if pd.isna(val):
        return ""
    if isinstance(val, str):
        return ""
    color = "#4ade80" if val >= 0 else "#f87171"
    return f"color: {color}; font-weight: 600;"

styled = display_df.style.map(style_returns, subset=period_labels)
styled = styled.format({c: "{:+.2f}%" for c in period_labels}, na_rep="N/A")
st.dataframe(styled, use_container_width=True, height=560)
