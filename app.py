import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import os
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Universal Stock Momentum Screener", layout="wide", page_icon="🎯")

# 🔄 ஒவ்வொரு 15 நொடிகளுக்கும் பக்கம் தானாகப் புதுப்பிக்கப்படும்
count = st_autorefresh(interval=15 * 1000, key="stock_feed_refresh")

CSV_FILE = "paper_trades.csv"
TELEGRAM_BOT_TOKEN = "9137625560:AAFnBFjBmw6B4M1JgtXXzV2OTqqBjkCpUUA"
TELEGRAM_CHAT_ID = "9266645987"

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception:
        pass

# நேரக் கட்டுப்பாடு (IST)
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

# 📊 Large, Mid & High-Volume Low Level Stocks (மொத்தம் 90+ பங்குகள்)
WATCHLIST = [
    # --- முன்னணி Large Cap பங்குகள் ---
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS", "NTPC.NS",
    "ONGC.NS", "POWERGRID.NS", "TATASTEEL.NS", "COALINDIA.NS", "M&M.NS",
    
    # --- சிறந்த Mid-Cap பங்குகள் ---
    "TRENT.NS", "BEL.NS", "HAL.NS", "VEDL.NS", "POLYCAB.NS",
    "PERSISTENT.NS", "COFORGE.NS", "DIXON.NS", "ASHOKLEY.NS", "BUMPER.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUROPHARMA.NS", "LUPIN.NS", "CANBK.NS",
    "BANKBARODA.NS", "INDIANB.NS", "UNIONBANK.NS", "VOLTAS.NS", "TATACHEM.NS",
    "TATACOMM.NS", "EXIDEIND.NS", "AMBUJACEM.NS", "ACC.NS", "TATAPOWER.NS",
    "JSWENERGY.NS", "NHPC.NS", "SJVN.NS", "BHEL.NS", "NMDC.NS",
    
    # --- அதிக மூவ்மென்ட் தரும் Low-Level / Penny / High-Volume பங்குகள் ---
    "SUZLON.NS", "IDEA.NS", "YESBANK.NS", "ZOMATO.NS", "IRFC.NS",
    "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "NBCC.NS", "HUDCO.NS",
    "IOC.NS", "GAIL.NS", "SAIL.NS", "PNB.NS", "UCOBANK.NS",
    "IOB.NS", "CENTRALBK.NS", "MAHABANK.NS", "RPOWER.NS", "JPPOWER.NS",
    "RENUKA.NS", "GTLINFRA.NS", "HFCL.NS", "IFCI.NS", "SOUTHBANK.NS"
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

# அதிவேக Batch Data Download (ஒரே நேரத்தில் அனைத்து பங்குகளின் விலையையும் எடுக்கும்)
@st.cache_data(ttl=10)
def scan_all_stocks():
    results = []
    try:
        data = yf.download(
            tickers=" ".join(WATCHLIST),
            period="5d",
            interval="15m",
            group_by="ticker",
            progress=False,
            auto_adjust=True
        )
        for ticker in WATCHLIST:
            try:
                df = data[ticker].dropna() if len(WATCHLIST) > 1 else data.dropna()
                if len(df) >= 5:
                    curr_price = round(float(df['Close'].iloc[-1]), 2)
                    prev_price = float(df['Close'].iloc[-5])
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
    except Exception:
        pass
    return pd.DataFrame(results)

with st.spinner("Large, Mid & Low level பங்குகள் ஸ்கேன் செய்யப்படுகின்றன..."):
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
        
