import streamlit as st
import pandas as pd
import time
from datetime import datetime
from iqoptionapi.stable_api import IQ_Option

st.set_page_config(page_title="FINAL BOSS LIVE", layout="centered")

# ===== STYLE =====
st.markdown("""
<style>
body {background: linear-gradient(135deg,#020617,#0f172a); color:#e2e8f0;}
h1 {text-align:center;color:#22c55e;}
.card {
background:#020617;
padding:20px;
border-radius:15px;
box-shadow:0 0 25px rgba(0,255,200,0.1);
margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

# ===== LOGIN UI =====
st.title("💀 FINAL BOSS LIVE IQ SNIPER")

email = st.text_input("IQ Option Email")
password = st.text_input("IQ Option Password", type="password")

connect_btn = st.button("🔗 CONNECT")

if "iq" not in st.session_state:
    st.session_state.iq = None

if connect_btn:
    iq = IQ_Option(email, password)
    iq.connect()

    if iq.check_connect():
        st.success("✅ Connected to IQ Option")
        iq.change_balance("PRACTICE")
        st.session_state.iq = iq
    else:
        st.error("❌ Connection Failed")

# ===== ASSETS =====
ASSETS = [
    "EURUSD-OTC","GBPUSD-OTC","USDJPY-OTC",
    "AUDUSD-OTC","EURJPY-OTC","GBPJPY-OTC",
    "USDCHF-OTC","NZDUSD-OTC"
]

# ===== GET CANDLES =====
def get_data(asset):
    try:
        iq = st.session_state.iq
        candles = iq.get_candles(asset, 60, 50, time.time())

        df = pd.DataFrame(candles)
        df = df.rename(columns={
            "open":"Open","close":"Close",
            "min":"Low","max":"High"
        })

        df = df[["Open","High","Low","Close"]]
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df.reset_index(drop=True, inplace=True)

        return df
    except:
        return None

# ===== INDICATORS =====
def add_indicators(df):
    df["EMA"] = df["Close"].ewm(span=20).mean()
    df["EMA_FAST"] = df["Close"].ewm(span=5).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = (100-(100/(1+rs))).fillna(50)

    return df

# ===== ANALYSIS =====
def analyze(asset):
    df = get_data(asset)
    if df is None or len(df) < 30:
        return None

    try:
        df = add_indicators(df)

        c = float(df["Close"].iloc[-1])
        ema = float(df["EMA"].iloc[-1])
        ema_fast = float(df["EMA_FAST"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])

        trend = "UP" if ema_fast > ema else "DOWN"

        last_open = float(df["Open"].iloc[-1])
        last_close = float(df["Close"].iloc[-1])

        candle_up = last_close > last_open

        buy = 0
        sell = 0

        if trend == "UP": buy += 2
        else: sell += 2

        if rsi < 45: buy += 1
        elif rsi > 55: sell += 1

        if candle_up: buy += 1
        else: sell += 1

        direction = "BUY 📈" if buy >= sell else "SELL 📉"
        confidence = min(95, 78 + max(buy,sell)*3)

        return direction, confidence

    except:
        return None

# ===== BEST SIGNAL =====
def best_signal():
    best = None
    best_score = -1

    for asset in ASSETS:
        result = analyze(asset)
        if not result:
            continue

        direction, confidence = result

        score = confidence

        if score > best_score:
            best = (asset, direction, confidence)
            best_score = score

    if best is None:
        return (
            ASSETS[0],
            "BUY 📈",
            80
        )

    return best

# ===== TIMER =====
def entry_time():
    sec = datetime.now().second
    return 60 - sec if sec > 5 else sec

# ===== HISTORY =====
if "history" not in st.session_state:
    st.session_state.history = []

# ===== SIGNAL BUTTON =====
if st.button("🎯 GET LIVE SIGNAL"):

    if st.session_state.iq is None:
        st.warning("⚠️ Connect first")
    else:
        pair, direction, confidence = best_signal()
        wait = entry_time()

        st.markdown(f"""
        <div class="card">
        <h2>{pair}</h2>
        <h3>{direction}</h3>
        ⏳ Entry: {wait} sec<br>
        🔥 Confidence: {confidence}%
        </div>
        """, unsafe_allow_html=True)

        for i in range(wait, -1, -1):
            st.write(f"⏳ {i}s")
            time.sleep(1)

        st.session_state.history.insert(0, {
            "pair":pair,
            "dir":direction,
            "conf":confidence
        })

# ===== HISTORY =====
st.subheader("📜 Signal History")
for h in st.session_state.history:
    st.write(h)
