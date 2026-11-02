import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import pytz
import os
import requests
from streamlit_autorefresh import st_autorefresh

# திரையை முழு அகலத்தில் (Wide Layout) காட்ட அமைத்துள்ளோம்
st.set_page_config(page_title="Stock Momentum Screener", layout="wide", page_icon="🎯")

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

st.title("🎯 AI Live Stock Dashboard")
st.caption(f"🔄 தானியங்கி புதுப்பிப்பு: **{current_time_str}** | சுழற்சி: #{count}")

if 9.5 <= time_decimal < 14.5:
    st.success(f"🟢 நேரம்: {current_time_str} | [BEST TRADING ZONE] என்ட்ரி எடுக்க உகந்த நேரம்.")
elif 9.25 <= time_decimal < 9.5:
    st.error(f"⚠️ நேரம்: {current_time_str} | [NO TRADE ZONE] சந்தை நிலையற்ற நேரம். தவிர்க்கவும்!")
else:
    st.warning(f"🕒 நேரம்: {current_time_str} | மார்க்கெட் முடிவடைந்தது / ஓய்வு நேரம்.")

st.markdown("---")

# Large, Mid & Penny / High-Volume பங்குகள் பட்டியல்
WATCHLIST = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "TATAMOTORS.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "LT.NS",
    "KOTAKBANK.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
    "TITAN.NS", "BAJFINANCE.NS", "WIPRO.NS", "HCLTECH.NS", "NTPC.NS",
    "ONGC.NS", "POWERGRID.NS", "TATASTEEL.NS", "COALINDIA.NS", "M&M.NS",
    "TRENT.NS", "BEL.NS", "HAL.NS", "VEDL.NS", "POLYCAB.NS",
    "PERSISTENT.NS", "COFORGE.NS", "DIXON.NS", "ASHOKLEY.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "AUROPHARMA.NS", "LUPIN.NS", "CANBK.NS",
    "BANKBARODA.NS", "INDIANB.NS", "UNIONBANK.NS", "VOLTAS.NS", "TATACHEM.NS",
    "TATAPOWER.NS", "JSWENERGY.NS", "NHPC.NS", "SJVN.NS", "BHEL.NS", "NMDC.NS",
    "SUZLON.NS", "IDEA.NS", "YESBANK.NS", "ZOMATO.NS", "IRFC.NS",
    "RVNL.NS", "IRCON.NS", "RAILTEL.NS", "NBCC.NS", "HUDCO.NS",
    "IOC.NS", "GAIL.NS", "SAIL.NS", "PNB.NS", "UCOBANK.NS",
    "IOB.NS", "CENTRALBK.NS", "MAHABANK.NS", "RPOWER.NS", "JPPOWER.NS",
    "RENUKA.NS", "HFCL.NS", "IFCI.NS", "SOUTHBANK.NS"
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

                    status = "NEUTRAL"
                    if pct > 0.4:
                        status = "POSITIVE"
                    elif pct < -0.4:
                        status = "NEGATIVE"

                    results.append({
                        "Ticker": ticker,
                        "Live Price": curr_price,
                        "Change %": pct,
                        "Status": status
                    })
            except Exception:
                continue
    except Exception:
        pass
    return pd.DataFrame(results)

with st.spinner("அனைத்து பங்குகளையும் ஸ்கேன் செய்கிறது..."):
    df_market = scan_all_stocks()

pos_df = df_market[df_market["Status"] == "POSITIVE"] if not df_market.empty else pd.DataFrame()
neg_df = df_market[df_market["Status"] == "NEGATIVE"] if not df_market.empty else pd.DataFrame()
neu_df = df_market[df_market["Status"] == "NEUTRAL"] if not df_market.empty else pd.DataFrame()

# 📱 திரையை இடமிருந்து வலமாக 3 பக்கவாட்டுப் பத்திகளாக (3 Columns) பிரிக்கிறோம்
col_left, col_mid, col_right = st.columns(3)

# ---------------------------------------------------------
# 🟢 இடதுபுறம் (Left): POSITIVE MOMENTUM (BUY)
# ---------------------------------------------------------
with col_left:
    st.subheader("🟢 Positive (BUY)")
    if not pos_df.empty:
        for idx, row in pos_df.iterrows():
            ticker = row["Ticker"]
            price = row["Live Price"]
            pct = row["Change %"]
            is_held = ticker in held_stocks
            target = round(price * 1.02, 2)
            sl = round(price * 0.99, 2)

            st.markdown(f"**{ticker}** {'💼 *(Holding)*' if is_held else ''}")
            st.markdown(f"🟢 **₹{price}** (+{pct}%)")
            if st.button(f"🚀 BUY (T: ₹{target} | SL: ₹{sl})", key=f"pos_{idx}", use_container_width=True):
                new_row = pd.DataFrame([{
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticker": ticker, "Action": "BUY", "Current_Price": price,
                    "Entry": price, "Target": target, "Stop_Loss": sl,
                    "Status": "OPEN", "Simulated_PnL": 0.0
                }])
                new_row.to_csv(CSV_FILE, mode="a", index=False, header=not os.path.exists(CSV_FILE))
                send_telegram(f"🟢 *BUY Triggered!*\nStock: `{ticker}`\nPrice: ₹{price}\nTarget: ₹{target}\nSL: ₹{sl}")
                st.rerun()
            st.divider()
    else:
        st.info("பாசிட்டிவ் பங்குகள் இல்லை.")

# ---------------------------------------------------------
# 🔴 நடுவில் (Middle): NEGATIVE MOMENTUM (SELL)
# ---------------------------------------------------------
with col_mid:
    st.subheader("🔴 Negative (SELL)")
    if not neg_df.empty:
        for idx, row in neg_df.iterrows():
            ticker = row["Ticker"]
            price = row["Live Price"]
            pct = row["Change %"]
            is_held = ticker in held_stocks

            st.markdown(f"**{ticker}** {'💼 *(Holding)*' if is_held else ''}")
            st.markdown(f"🔴 **₹{price}** ({pct}%)")
            if is_held:
                if st.button(f"🔴 Exit / SELL", key=f"neg_{idx}", use_container_width=True):
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
                st.caption("🛑 டவுன்ட்ரெண்ட் (Avoid Buying)")
            st.divider()
    else:
        st.info("நெகட்டிவ் பங்குகள் இல்லை.")

# ---------------------------------------------------------
# 🟡 வலதுபுறம் (Right): NO MOVEMENT (NEUTRAL)
# ---------------------------------------------------------
with col_right:
    st.subheader("🟡 Neutral (No Move)")
    if not neu_df.empty:
        st.caption(f"மொத்தம்: {len(neu_df)} பங்குகள்")
        st.dataframe(neu_df[["Ticker", "Live Price", "Change %"]], use_container_width=True, height=450)
    else:
        st.info("அனைத்திலும் மொமண்டம் உள்ளது.")

st.markdown("---")
st.subheader("📊 தற்போது இயங்கும் டிரேடுகள் (Open Positions)")
if os.path.exists(CSV_FILE):
    try:
        df_open = pd.read_csv(CSV_FILE)
        st.dataframe(df_open, use_container_width=True)
    except Exception:
        pass
