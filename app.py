import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Page config for clean look matching your dark theme
st.set_page_config(page_title="Market Performance", layout="centered")

st.title("📊 Market Performance Dashboard")
st.write("Real-time updates across major asset classes.")

# Define assets and their Yahoo Finance tickers
assets = {
    "Nifty 50": "^NSEI",
    "Nifty Bank": "^NSEBANK",
    "Nasdaq": "^IXIC",
    "S&P 500": "^GSPC",
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "KOSPI": "^KS11",
    "Karachi 100": "^KSE",
    "USD-INR": "INR=X",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F",
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Dogecoin": "DOGE-USD"
}


@st.cache_data(ttl=3600)  # Cache data for 1 hour to keep it fast
def get_performance_data():
    table_data = []

    for name, ticker in assets.items():
        # Fetch up to 11 years to safely calculate 10-year lookbacks
        data = yf.download(ticker, start=datetime.now() - timedelta(days=11 * 365), end=datetime.now(), progress=False)
        if data.empty:
            continue

        current_price = data['Close'].iloc[-1].item()

        # Helper function to extract historical prices safely
        def calc_return(days_ago):
            try:
                # Use the latest date in the data's index to match timezones safely
                target_date = data.index[-1] - pd.Timedelta(days=days_ago)
                
                # Get the last available price on or before that target date
                past_price = data['Close'].loc[:target_date].iloc[-1].item()
                
                return f"{((current_price - past_price) / past_price) * 100:+.2f}%"
            except:
                return "N/A"

        # Safe extraction for last trading day change
        try:
            prev_close = data['Close'].iloc[-2].item()
            day_return = f"{((current_price - prev_close) / prev_close) * 100:+.2f}%"
        except:
            day_return = "N/A"

        table_data.append({
            "Asset Class": name,
            "Latest Price": f"{current_price:,.2f}",
            "Last Day": day_return,
            "1 Week": calc_return(7),
            "1 Month": calc_return(30),
            "1 Year": calc_return(365),
            "2 Year": calc_return(2 * 365),
            "3 Year": calc_return(3 * 365),
            "5 Year": calc_return(5 * 365),
            "10 Year": calc_return(10 * 365)
        })

    return pd.DataFrame(table_data)


df = get_performance_data()
st.dataframe(df.set_index("Asset Class"), width="stretch")
st.caption("Data sourced automatically via Yahoo Finance. Absolute returns calculated relative to current date.")
