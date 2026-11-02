import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import os
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Universal Stock Momentum Screener", layout="wide", page_icon="🎯")

# 🔄 ஒவ்வொரு 10 நொடிகளுக்கும் பக்கம் தானாகப் புதுப்பிக்கப்படும்
count = st_autorefresh(interval=10 * 1000, key="stock_feed_refresh")

CSV_FILE = "paper_trades.csv"
TELEGRAM_BOT_TOKEN = "9137625560:AAFnBFjBmw6B4M1JgtXXzV2OTqqBjkCpUUA"
TELEGRAM_CHAT_ID = "9266645987"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

# நேரக் கட்டுப்பாடு
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
current_time_str = now.strftime("%I:%M:%S %p")
time_decimal = now.hour + (now.minute / 60.0)

st.title("🎯 All-Stocks AI Momentum Dashboard")
st.caption(f"🔄 நேரலை தானியங்கி அப்டேட்: **{current_time_str}** | புதுப்பிப்புகள்: #{count}")

if 9.5 <= time_decimal < 14.5:
    st.success(f"🟢 நேரம்: {current_time_str} | [BEST TRADING ZONE] என்ட்ரி எடுக்க உகந்த நேரம்.")
elif 9.25 <= time_decimal < 9.5:
    st.error(f"⚠️ நேரம்: {current_time_str} | [NO TRADE ZONE] மார்க்கெட் நிலையற்ற நேரம். ஆர்டர் எடுக்க வேண்டாம்!")
else:
    st.warning(f"🕒 நேரம்: {current_time_str} | வர்த்தக நேரம் அல்ல / மார்க்கெட் முடிவடைந்தது.")

st.markdown("---")

WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "LT.NS",
    "TATAMOTORS.NS", "ITC.NS", "SBIN.NS", "IOC.NS", "ONGC.NS",
    "BEL.NS", "PNB.NS", "SAIL.NS", "ZOMATO.NS", "SUZLON.NS"
]

held_stocks = []
if os.path.exists(CSV_FILE):
    try:
        df_existing = pd.read_csv(CSV_FILE)
        if "Status" in df_existing.columns and "Action" in df_existing.columns:
            open_buys = df_existing[(df_existing["Status"] == "OPEN") & (df_existing["Action"] == "BUY")]
            held_stocks = open_buys["Ticker"].tolist()
    except Exception:
        pass

@st.cache_data(ttl=5)
def scan_all_stocks():
    results = []
    for ticker in WATCHLIST:
        try:
            t = yf.Ticker(ticker)
            df = t.history(period="5d", interval="15m")
            if len(df) >= 5:
                curr_price = round(df['Close'].iloc[-1], 2)
                prev_price = df['Close'].iloc[-5]
                pct = round(((curr_price - prev_price) / prev_price) * 100, 2)

                results.append({
                    "Ticker": ticker,
                    "Live Price": curr_price,
                    "Change %": pct,
                    "Is_Positive": pct > 0.4,
                    "Is_Negative": pct < -0.4
                })
        except Exception:
            continue
    return pd.DataFrame(results)

df_market = scan_all_stocks()

st.subheader("📋 நேரலை சிக்னல்கள் (Live Signals)")

if not df_market.empty:
    for idx, row in df_market.iterrows():
        ticker = row["Ticker"]
        price = row["Live Price"]
        pct = row["Change %"]
        is_held = ticker in held_stocks

        col1, col2, col3 = st.columns([3, 3, 4])
        col1.markdown(f"**{ticker}** {'💼 *(Holding)*' if is_held else ''}")
        col2.markdown(f"₹{price} ({'+' if pct > 0 else ''}{pct}%)")

        if row["Is_Positive"]:
            target = round(price * 1.02, 2)
            sl = round(price * 0.99, 2)
            if col3.button(f"🟢 1-Click BUY (Target: ₹{target} | SL: ₹{sl})", key=f"buy_{idx}"):
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticker": ticker, "Action": "BUY", "Current_Price": price,
                    "Entry": price, "Target": target, "Stop_Loss": sl,
                    "Status": "OPEN", "Simulated_PnL": 0.0
                }])
                new_row.to_csv(CSV_FILE, mode="a", index=False, header=not os.path.exists(CSV_FILE))
                send_telegram(f"🟢 *BUY Triggered!*\nStock: `{ticker}`\nPrice: ₹{price}\nTarget: ₹{target}\nSL: ₹{sl}")
                st.rerun()

        elif row["Is_Negative"]:
            if is_held:
                if col3.button(f"🔴 1-Click SELL (Exit Position)", key=f"sell_{idx}"):
                    new_row = pd.DataFrame([{
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Ticker": ticker, "Action": "SELL", "Current_Price": price,
                        "Entry": price, "Target": round(price * 0.98, 2), "Stop_Loss": round(price * 1.01, 2),
                        "Status": "OPEN", "Simulated_PnL": 0.0
                    }])
                    new_row.to_csv(CSV_FILE, mode="a", index=False, header=not os.path.exists(CSV_FILE))
                    send_telegram(f"🔴 *SELL / EXIT Triggered!*\nStock: `{ticker}`\nExit Price: ₹{price}")
                    st.rerun()
            else:
                col3.error("🛑 DON'T BUY (Negative Trend)")
        else:
            col3.info("⚪ WAIT (No Momentum)")
        
        st.divider()

st.subheader("📊 தற்போது இயங்கும் டிரேடுகள் (Open Positions)")
if os.path.exists(CSV_FILE):
    try:
        df_open = pd.read_csv(CSV_FILE)
        st.dataframe(df_open, use_container_width=True)
    except Exception:
        pass
