import streamlit as st
import pandas as pd
import yfinance as yf
import random
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="FINAL BOSS AI", layout="centered")

# ================= STYLE =================
st.markdown("""
<style>
body { background-color: #0d1117; }
.main {
    background: linear-gradient(135deg, #0d1117, #161b22);
    color: #e6edf3;
}
h1 { color: #00ffcc; text-align: center; }
.stButton>button {
    background: linear-gradient(90deg, #00ffcc, #0077ff);
    color: black;
    border-radius: 10px;
    font-weight: bold;
    height: 3em;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

# ================= DATA =================
PAIRS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "CAD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X"
}

# ================= SESSION =================
def get_wat_time():
    return datetime.now(timezone.utc) + timedelta(hours=1)

def get_session():
    h = get_wat_time().hour
    if 7 <= h < 13:
        return "LONDON 🔥"
    elif 13 <= h < 18:
        return "NEW YORK ⚡"
    return "LOW MARKET 💤"

def get_entry_time():
    sec = get_wat_time().second
    return sec if sec <= 10 else 60-sec

# ================= NOTIFY =================
def notify():
    st.markdown("""
    <script>
    var audio = new Audio("https://www.soundjay.com/buttons/sounds/button-3.mp3");
    audio.play();
    alert("🚨 SNIPER SIGNAL READY!");
    </script>
    """, unsafe_allow_html=True)

# ================= DATA FETCH =================
def get_data(symbol):
    try:
        df = yf.download(symbol, interval="1m", period="1d", progress=False)
        if df is None or df.empty or len(df) < 30:
            return None
        df = df[['Open','High','Low','Close']].dropna().reset_index(drop=True)
        return df.tail(50)
    except:
        return None

# ================= INDICATORS =================
def rsi(df, p=14):
    d = df["Close"].diff()
    gain = d.clip(lower=0).rolling(p).mean()
    loss = -d.clip(upper=0).rolling(p).mean()
    rs = gain / loss
    return (100 - (100/(1+rs))).fillna(50)

def pattern(df):
    if len(df) < 2: return "NONE"
    a, b = df.iloc[-1], df.iloc[-2]

    if b["Close"] < b["Open"] and a["Close"] > a["Open"]:
        return "BULLISH 📈"
    if b["Close"] > b["Open"] and a["Close"] < a["Open"]:
        return "BEARISH 📉"
    return "NONE"

def entry_confirmation(df, direction):
    last = df.iloc[-1]
    if direction == "CALL 📈":
        return last["Close"] > last["Open"]
    if direction == "PUT 📉":
        return last["Close"] < last["Open"]
    return False

# ================= ANALYSIS =================
def analyze(symbol):
    df = get_data(symbol)
    if df is None: return None

    df["EMA"] = df["Close"].ewm(span=20).mean()
    df["RSI"] = rsi(df)

    trend = "UPTREND" if df["Close"].iloc[-1] > df["EMA"].iloc[-1] else "DOWNTREND"
    pat = pattern(df)
    rsi_val = df["RSI"].iloc[-1]

    return df, trend, pat, rsi_val

# ================= SIGNAL =================
def best_signal():
    best = None
    best_score = 0

    for name, sym in PAIRS.items():
        r = analyze(sym)
        if not r: continue

        df, trend, pat, rsi_val = r

        call = 0
        put = 0

        if trend == "UPTREND": call += 2
        else: put += 2

        if rsi_val < 45: call += 1
        elif rsi_val > 55: put += 1

        if "BULLISH" in pat: call += 2
        elif "BEARISH" in pat: put += 2

        direction = None
        if call > put: direction = "CALL 📈"
        elif put > call: direction = "PUT 📉"

        if not direction: continue
        if not entry_confirmation(df, direction): continue

        score = max(call, put)
        wait = get_entry_time()

        if wait > 50: continue

        if score > best_score:
            best = {
                "pair": name,
                "dir": direction,
                "wait": wait,
                "confidence": min(99, 80 + score*3)
            }
            best_score = score

    return best

# ================= HISTORY =================
if "history" not in st.session_state:
    st.session_state.history = []

# ================= UI =================
st.markdown("<h1>💀 FINAL BOSS AI</h1>", unsafe_allow_html=True)
st.markdown(f"🕒 {get_wat_time().strftime('%H:%M:%S')} (WAT)")
st.markdown(f"📊 {get_session()}")

auto = st.toggle("🔄 AUTO SCAN (LIVE)", value=False)

# ================= AUTO LOOP =================
if auto:
    placeholder = st.empty()
    while True:
        s = best_signal()

        with placeholder.container():
            if s:
                notify()
                st.success("🚨 SNIPER SIGNAL")

                st.markdown(f"""
                ### {s['pair']}
                🎯 {s['dir']}
                ⏱ Entry: {s['wait']}s
                🔥 Confidence: {s['confidence']}%
                """)

                st.session_state.history.insert(0, s)
                st.session_state.history = st.session_state.history[:10]

            else:
                st.warning("No setup")

        time.sleep(5)
        st.rerun()

# ================= MANUAL =================
if st.button("🎯 GET SIGNAL"):
    s = best_signal()

    if s:
        notify()
        st.success("🚨 SNIPER SIGNAL")

        st.markdown(f"""
        ### {s['pair']}
        🎯 {s['dir']}
        ⏱ Entry: {s['wait']}s
        🔥 Confidence: {s['confidence']}%
        """)

        st.session_state.history.insert(0, s)
        st.session_state.history = st.session_state.history[:10]

    else:
        st.warning("No setup")

# ================= HISTORY PANEL =================
st.markdown("---")
st.subheader("📜 SIGNAL HISTORY")

for h in st.session_state.history:
    st.markdown(f"""
    {h['pair']} | {h['dir']} | ⏱ {h['wait']}s | 🔥 {h['confidence']}%
    """)
