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
    "USD-INR": "INR=X",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Crude Oil": "CL=F"
}

@st.cache_data(ttl=3600)  # Cache data for 1 hour to keep it fast
def get_performance_data():
    table_data = []
    
    for name, ticker in assets.items():
        # Fetch up to 12 years of data to ensure enough history for the 10-year lookback
        data = yf.download(ticker, start=datetime.now() - timedelta(days=12*365), end=datetime.now(), progress=False)
        if data.empty:
            continue
        
        # FIX: Flatten MultiIndex columns if present (handles newer yfinance version quirks)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # Core Safety Fix: Strip timezone info so all asset dates compare perfectly
        data.index = data.index.tz_localize(None)
        
        current_price = float(data['Close'].iloc[-1])
        
        # Bulletproof historical lookup
        def calc_return(days_ago):
            try:
                target_date = datetime.now() - timedelta(days=days_ago)
                # Filter for all trading days that occurred on or before the target date
                past_trading_days = data[data.index <= target_date]
                if past_trading_days.empty:
                    return "N/A"
                # Grab the closest available trading day's closing price
                past_price = float(past_trading_days['Close'].iloc[-1])
                return f"{((current_price - past_price) / past_price) * 100:+.2f}%"
            except:
                return "N/A"

        # Safe extraction for last trading day change
        try:
            prev_close = float(data['Close'].iloc[-2])
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
            "2 Year": calc_return(2*365),
            "3 Year": calc_return(3*365),
            "5 Year": calc_return(5*365),
            "10 Year": calc_return(10*365)
        })
        
    return pd.DataFrame(table_data)

df = get_performance_data()
st.dataframe(df.set_index("Asset Class"), use_container_width=True)
st.caption("Data sourced automatically via Yahoo Finance. Absolute returns calculated relative to current date.")
