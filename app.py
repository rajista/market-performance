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
st.set_page_config(
    page_title="Global Market Pulse",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------------------------
# DARK THEME + MOBILE OPTIMIZATIONS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #e2e8f0; }
    h1, h2, h3 { color: #f1f5f9 !important; }
    .sub-header { color: #64748b; font-size: 0.95rem; margin-top: -10px; }

    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, #131a27, #0f1117);
        border: 1px solid #1e293b; border-radius: 12px; padding: 14px 16px;
    }

    .ticker-strip {
        white-space: nowrap; overflow-x: auto; background:#131a27;
        border:1px solid #1e293b; border-radius:8px; padding:8px 0; margin-bottom:18px;
    }
    .ticker-item { display:inline-block; padding:0 18px; font-size:0.9rem; font-weight:600; }

    /* Mobile */
    @media (max-width: 768px) {
        .stPlotlyChart { overflow-x: auto !important; }
        .stPlotlyChart text { font-size: 9px !important; }
        .stColumn { padding: 0.4rem 0.4rem !important; }
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Global Market Pulse")
st.markdown('<p class="sub-header">Live global market snapshot — mobile optimized</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ASSETS & PERIODS
# ---------------------------------------------------------------------------
GROUPS = {
    "Equity Indices": {
        "Nifty 50": "^NSEI", "Nifty Bank": "^NSEBANK", "Nasdaq": "^IXIC",
        "S&P 500": "^GSPC", "Nikkei 225": "^N225", "Hang Seng": "^HSI",
        "KOSPI": "^KS11", "Karachi 100": "^KSE",
    },
    "Currencies": {"USD-INR": "INR=X"},
    "Commodities": {"Gold": "GC=F", "Silver": "SI=F", "Crude Oil": "CL=F"},
    "Crypto": {"Bitcoin": "BTC-USD", "Ethereum": "ETH-USD"},
}

ASSETS = {name: tkr for grp in GROUPS.values() for name, tkr in grp.items()}
NAME_TO_GROUP = {name: grp for grp, items in GROUPS.items() for name in items}

PERIODS = [
    ("Last Day", 1), ("1 Week", 7), ("1 Month", 30), ("3 Month", 91),
    ("1 Year", 365), ("2 Year", 730), ("3 Year", 1095),
    ("5 Year", 1825), ("10 Year", 3650),
]

# ---------------------------------------------------------------------------
# DATA FETCH (ROBUST)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_market_data():
    table_rows, returns_matrix, history = [], {}, {}
    for name, ticker in ASSETS.items():
        try:
            data = yf.download(ticker, period="max", progress=False, auto_adjust=True)
            if data.empty or len(data) < 5:
                continue
            close = data["Close"].dropna()
            if len(close) < 2:
                continue

            current_price = float(close.iloc[-1])
            history[name] = close

            def calc_return(days_ago):
                try:
                    if days_ago == 1:
                        past = float(close.iloc[-2])
                    else:
                        target = close.index[-1] - pd.Timedelta(days=days_ago)
                        past = float(close.asof(target))
                    return ((current_price - past) / past) * 100
                except:
                    return np.nan

            row = {"Asset": name, "Group": NAME_TO_GROUP.get(name, "Other"), "Latest Price": current_price}
            rmat = {}
            for label, days in PERIODS:
                val = calc_return(days)
                row[label] = val
                rmat[label] = val
            table_rows.append(row)
            returns_matrix[name] = rmat
        except:
            continue

    df = pd.DataFrame(table_rows)
    ret_df = pd.DataFrame(returns_matrix).T if returns_matrix else pd.DataFrame()
    return df, ret_df, history

with st.spinner("Fetching latest market data..."):
    df, ret_df, history = get_market_data()

if df.empty:
    st.error("⚠️ Unable to fetch market data right now. Please refresh.")
    st.stop()

period_labels = [p[0] for p in PERIODS]

# ---------------------------------------------------------------------------
# TICKER STRIP
# ---------------------------------------------------------------------------
strip_items = ""
for _, row in df.iterrows():
    val = row.get("Last Day", np.nan)
    if pd.isna(val): continue
    color = "#4ade80" if val >= 0 else "#f87171"
    arrow = "▲" if val >= 0 else "▼"
    strip_items += f'<span class="ticker-item">{row["Asset"]}: <span style="color:{color}">{arrow} {val:+.2f}%</span></span> '
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
        c.metric(asset, f"{r['Latest Price']:,.2f}", f"{r.get('Last Day', 0):+.2f}%")

st.divider()

# ---------------------------------------------------------------------------
# HEATMAP (Mobile Optimized)
# ---------------------------------------------------------------------------
st.subheader("🔥 Returns Heatmap")
st.caption("Green = Positive • Red = Negative • Scroll horizontally on mobile")

valid_assets = [a for a in df["Asset"] if a in ret_df.index]
heat_df = ret_df.loc[valid_assets, period_labels]

heat_values = heat_df.to_numpy(dtype=float)
finite = np.abs(heat_values[np.isfinite(heat_values)])
heat_limit = max(5.0, float(np.nanpercentile(finite, 90))) if len(finite) > 0 else 5.0

fig_height = max(520, len(heat_df) * 32)

fig_heat = go.Figure(go.Heatmap(
    z=heat_values, x=heat_df.columns, y=heat_df.index,
    colorscale=[[0,"#ff3333"],[0.45,"#4a1212"],[0.5,"#0f1117"],[0.55,"#123d24"],[1,"#00cc96"]],
    zmin=-heat_limit, zmax=heat_limit, zmid=0,
    text=np.round(heat_values,2), texttemplate="%{text:+.1f}%",
    textfont={"size":9.5}, hovertemplate="%{y}<br>%{x}: %{z:+.2f}%<extra></extra>"
))

fig_heat.update_layout(
    plot_bgcolor="#0b0e14", paper_bgcolor="#0b0e14",
    height=fig_height, margin=dict(l=8,r=8,t=35,b=25),
    xaxis=dict(tickangle=45, tickfont=dict(size=10), side="top"),
    yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
    font=dict(color="#e2e8f0", size=11)
)

st.plotly_chart(fig_heat, use_container_width=True, config={"responsive": True, "displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# 1-YEAR BAR (Mobile Optimized)
# ---------------------------------------------------------------------------
st.subheader("📈 1-Year Performance")
bar_df = df.dropna(subset=["1 Year"]).sort_values("1 Year", ascending=True).copy()
if not bar_df.empty:
    bar_df["1 Year"] = pd.to_numeric(bar_df["1 Year"])
    bar_height = max(520, len(bar_df) * 28)
    fig_bar = px.bar(bar_df, x="1 Year", y="Asset", color="Group", orientation="h",
                     text=bar_df["1 Year"].map(lambda x: f"{x:+.1f}%"))
    fig_bar.update_layout(height=bar_height, plot_bgcolor="#0b0e14", paper_bgcolor="#0b0e14",
                          margin=dict(l=10,r=60,t=30,b=20), font=dict(color="#e2e8f0"))
    st.plotly_chart(fig_bar, use_container_width=True, config={"responsive": True, "displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# PRICE TRENDS (Mobile Optimized)
# ---------------------------------------------------------------------------
st.subheader("📉 Price Trends (Last 6 Months)")
tabs = st.tabs(list(GROUPS.keys()))
for tab, group_name in zip(tabs, GROUPS.keys()):
    with tab:
        group_assets = [a for a in GROUPS[group_name] if a in history]
        cols = st.columns(min(3, len(group_assets) or 1))
        for i, asset in enumerate(group_assets):
            series = pd.to_numeric(history[asset], errors="coerce").dropna().tail(126)
            if len(series) < 10: continue
            change = ret_df.loc[asset, "1 Month"] if asset in ret_df.index else np.nan
            color = "#4ade80" if pd.notna(change) and change >= 0 else "#f87171"
            fig = go.Figure(go.Scatter(x=series.index, y=series.values, mode="lines",
                                       line=dict(color=color, width=2), fill="tozeroy"))
            fig.update_layout(height=140, margin=dict(l=0,r=0,t=32,b=0),
                              paper_bgcolor="#131a27", plot_bgcolor="#131a27",
                              title=f"{asset} • 1M: {change:+.1f}%" if pd.notna(change) else asset,
                              xaxis_visible=False, yaxis_visible=False)
            with cols[i % len(cols)]:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# FULL TABLE
# ---------------------------------------------------------------------------
st.subheader("📋 Full Performance Table")
display_df = df.set_index("Asset")[["Group", "Latest Price"] + period_labels].copy()
styled = display_df.style.format({c: "{:+.2f}%" for c in period_labels}, na_rep="N/A")
st.dataframe(styled, use_container_width=True, height=600)

st.caption("Data via Yahoo Finance • Refresh for latest • Horizontal scroll on mobile")
