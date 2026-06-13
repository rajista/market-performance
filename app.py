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
    initial_sidebar_state="collapsed"  # Better for mobile
)

# ---------------------------------------------------------------------------
# DARK THEME + COMPREHENSIVE MOBILE OPTIMIZATIONS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { 
        background-color: #0b0e14; 
        color: #e2e8f0; 
    }
    h1, h2, h3 { 
        color: #f1f5f9 !important; 
        font-family: 'Segoe UI', sans-serif; 
    }
    .sub-header { 
        color: #64748b; 
        font-size: 0.95rem; 
        margin-top: -10px; 
    }

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

    /* Tabs */
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #facc15 !important; }

    /* Dataframe */
    div[data-testid="stDataFrame"] { 
        border: 1px solid #1e293b; 
        border-radius: 10px; 
    }

    /* Insight cards */
    .insight-card {
        background: #131a27; 
        border: 1px solid #1e293b; 
        border-radius: 10px;
        padding: 14px 16px; 
        margin-bottom: 10px; 
        font-size: 0.92rem; 
        color: #cbd5e1;
    }
    .insight-tag {
        display:inline-block; 
        padding:2px 8px; 
        border-radius:6px; 
        font-size:0.75rem;
        font-weight:700; 
        margin-right:8px;
    }
    .tag-pos { background:#16302180; color:#4ade80; }
    .tag-neg { background:#3f1d1d80; color:#f87171; }
    .tag-neu { background:#1e293b; color:#facc15; }

    .ticker-strip {
        white-space: nowrap; 
        overflow-x: auto; 
        background:#131a27;
        border:1px solid #1e293b; 
        border-radius:8px; 
        padding:8px 0; 
        margin-bottom:18px;
    }
    .ticker-item { 
        display:inline-block; 
        padding:0 18px; 
        font-size:0.9rem; 
        font-weight:600; 
    }

    /* MOBILE OPTIMIZATIONS */
    @media (max-width: 768px) {
        .stPlotlyChart {
            overflow-x: auto !important;
            max-width: 100%;
        }
        .stPlotlyChart text, .stPlotlyChart .xtick, .stPlotlyChart .ytick {
            font-size: 9px !important;
        }
        div[data-testid="stPlotlyChart"] {
            padding: 4px 0 !important;
        }
        .stMarkdown h2, .stMarkdown h3 {
            font-size: 1.4rem !important;
        }
        /* Reduce column padding on mobile */
        .stColumn {
            padding: 0.5rem 0.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Global Market Pulse")
st.markdown('<p class="sub-header">Live snapshot across global markets — optimized for mobile & desktop</p>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# ASSET UNIVERSE
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
    ("Last Day", 1), ("1 Week", 7), ("1 Month", 30), ("3 Month", 91),
    ("1 Year", 365), ("2 Year", 730), ("3 Year", 1095),
    ("5 Year", 1825), ("10 Year", 3650),
]

# ---------------------------------------------------------------------------
# DATA FETCH
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
            current_price = float(close.iloc[-1])
            history[name] = close

            def calc_return(days_ago):
                try:
                    if days_ago == 1:
                        past = float(close.iloc[-2])
                    else:
                        target = close.index[-1] - pd.Timedelta(days=days_ago)
                        past = float(close.loc[:target].iloc[-1])
                    return ((current_price - past) / past) * 100
                except:
                    return np.nan

            row = {"Asset": name, "Group": NAME_TO_GROUP[name], "Latest Price": current_price}
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
    ret_df = pd.DataFrame(returns_matrix).T
    return df, ret_df, history


with st.spinner("Fetching latest market data..."):
    df, ret_df, history = get_market_data()

period_labels = [p[0] for p in PERIODS]

# ---------------------------------------------------------------------------
# TICKER STRIP
# ---------------------------------------------------------------------------
strip_items = ""
for _, row in df.iterrows():
    val = row.get("Last Day", np.nan)
    if pd.isna(val):
        continue
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
# QUICK INSIGHTS
# ---------------------------------------------------------------------------
st.subheader("🧠 Quick Insights")
insights = []

day_df = df.dropna(subset=["Last Day"])
if not day_df.empty:
    best = day_df.loc[day_df["Last Day"].idxmax()]
    worst = day_df.loc[day_df["Last Day"].idxmin()]
    insights.append(("pos", f"<b>{best['Asset']}</b> leads today (+<b>{best['Last Day']:.2f}%</b>)"))
    insights.append(("neg", f"<b>{worst['Asset']}</b> lags today (<b>{worst['Last Day']:.2f}%</b>)"))

yr_df = df.dropna(subset=["1 Year"])
if not yr_df.empty:
    best_y = yr_df.loc[yr_df["1 Year"].idxmax()]
    insights.append(("pos", f"1Y leader: <b>{best_y['Asset']}</b> (+<b>{best_y['1 Year']:.2f}%</b>)"))

for tag, text in insights:
    cls = {"pos": "tag-pos", "neg": "tag-neg", "neu": "tag-neu"}.get(tag, "tag-neu")
    label = {"pos": "UP", "neg": "DOWN"}.get(tag, "NOTE")
    st.markdown(f'<div class="insight-card"><span class="insight-tag {cls}">{label}</span>{text}</div>', unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# RETURNS HEATMAP — MOBILE OPTIMIZED
# ---------------------------------------------------------------------------
st.subheader("🔥 Returns Heatmap")
st.caption("Green = Positive | Red = Negative • Scroll horizontally on mobile")

heat_df = ret_df[period_labels].copy()
heat_df = heat_df.loc[[a for a in df["Asset"] if a in heat_df.index]]

heat_values = heat_df.to_numpy(dtype=float)
finite_vals = np.abs(heat_values[np.isfinite(heat_values)])
heat_limit = max(5.0, float(np.nanpercentile(finite_vals, 90))) if len(finite_vals) > 0 else 5.0

num_assets = len(heat_df)
fig_height = max(520, num_assets * 32)  # Dynamic height

fig_heat = go.Figure(data=go.Heatmap(
    z=heat_values,
    x=heat_df.columns,
    y=heat_df.index,
    colorscale=[
        [0.0, "#ff3333"], [0.45, "#4a1212"], [0.5, "#0f1117"],
        [0.55, "#123d24"], [1.0, "#00cc96"]
    ],
    zmin=-heat_limit,
    zmax=heat_limit,
    zmid=0,
    text=np.round(heat_values, 2),
    texttemplate="%{text:+.1f}%",
    textfont={"size": 9.5},
    hovertemplate="%{y}<br>%{x}: %{z:+.2f}%<extra></extra>",
    colorbar=dict(title="Return %", thickness=12, len=0.7),
))

fig_heat.update_layout(
    plot_bgcolor="#0b0e14",
    paper_bgcolor="#0b0e14",
    font=dict(color="#e2e8f0", size=11),
    height=fig_height,
    margin=dict(l=8, r=8, t=35, b=25),
    xaxis=dict(tickangle=45, tickfont=dict(size=10), side="top"),
    yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
)

st.plotly_chart(
    fig_heat, 
    use_container_width=True, 
    config={"responsive": True, "scrollZoom": True, "displayModeBar": False}
)

st.divider()

# ---------------------------------------------------------------------------
# 1-YEAR BAR CHART — MOBILE OPTIMIZED
# ---------------------------------------------------------------------------
st.subheader("📈 1-Year Performance")

bar_df = df.dropna(subset=["1 Year"]).sort_values("1 Year", ascending=True).copy()
bar_df["1 Year"] = bar_df["1 Year"].astype(float)

bar_height = max(520, len(bar_df) * 28)  # Dynamic height

fig_bar = px.bar(
    bar_df, 
    x="1 Year", 
    y="Asset", 
    color="Group",
    orientation="h",
    text=bar_df["1 Year"].map(lambda x: f"{x:+.1f}%"),
    color_discrete_sequence=px.colors.qualitative.Bold
)

fig_bar.update_traces(
    textposition="outside",
    textfont=dict(size=11),
    cliponaxis=False
)

fig_bar.update_layout(
    plot_bgcolor="#0b0e14",
    paper_bgcolor="#0b0e14",
    font=dict(color="#e2e8f0", size=12),
    height=bar_height,
    margin=dict(l=10, r=80, t=30, b=20),
    xaxis_title="1-Year Return (%)",
    yaxis_title="",
    legend=dict(
        orientation="h", 
        yanchor="bottom", 
        y=1.02, 
        xanchor="right", 
        x=1,
        font=dict(size=11)
    ),
    xaxis=dict(zerolinecolor="#64748b", showgrid=False)
)

st.plotly_chart(fig_bar, use_container_width=True, config={"responsive": True, "displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# PRICE TRENDS — MOBILE OPTIMIZED
# ---------------------------------------------------------------------------
st.subheader("📉 Recent Price Trends (Last 6 Months)")

tab_names = list(GROUPS.keys())
tabs = st.tabs(tab_names)

for tab, group_name in zip(tabs, tab_names):
    with tab:
        group_assets = [a for a in GROUPS[group_name] if a in history]
        if not group_assets:
            st.info("No data available")
            continue
            
        # Mobile: max 2-3 columns
        num_cols = 2 if len(group_assets) > 3 else min(3, len(group_assets))
        cols = st.columns(num_cols)
        
        for i, asset in enumerate(group_assets):
            series = pd.to_numeric(history[asset], errors="coerce").dropna().tail(180)
            if len(series) < 10:
                continue
                
            change_1m = ret_df.loc[asset, "1 Month"] if asset in ret_df.index else np.nan
            line_color = "#4ade80" if pd.notna(change_1m) and change_1m >= 0 else "#f87171"
            
            fig_spark = go.Figure(go.Scatter(
                x=series.index,
                y=series.values,
                mode="lines",
                line=dict(color=line_color, width=2.2),
                fill="tozeroy",
                fillcolor="rgba(74,222,128,0.15)" if line_color == "#4ade80" else "rgba(248,113,113,0.15)"
            ))
            
            fig_spark.update_layout(
                height=135,
                margin=dict(l=0, r=0, t=32, b=0),
                paper_bgcolor="#131a27",
                plot_bgcolor="#131a27",
                title=dict(
                    text=f"{asset} • 1M: {change_1m:+.1f}%" if pd.notna(change_1m) else asset,
                    font=dict(size=12.5, color="#e2e8f0")
                ),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                showlegend=False
            )
            
            with cols[i % num_cols]:
                st.plotly_chart(fig_spark, use_container_width=True, config={"displayModeBar": False})

st.divider()

# ---------------------------------------------------------------------------
# FULL TABLE
# ---------------------------------------------------------------------------
st.subheader("📋 Complete Performance Table")

display_df = df.set_index("Asset")[["Group", "Latest Price"] + period_labels].copy()
display_df["Latest Price"] = display_df["Latest Price"].map(lambda x: f"{x:,.2f}")

def color_returns(val):
    if pd.isna(val):
        return ""
    color = "#4ade80" if val >= 0 else "#f87171"
    return f"color: {color}; font-weight: 600;"

styled_df = display_df.style.map(color_returns, subset=period_labels)
styled_df = styled_df.format({col: "{:+.2f}%" for col in period_labels}, na_rep="—")

st.dataframe(
    styled_df, 
    use_container_width=True, 
    height=620
)

st.caption("Data from Yahoo Finance • Updated hourly • Scroll table horizontally on mobile")
