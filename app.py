import streamlit as st
import pandas as pd
import yfinance as yf
import random
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="FINAL BOSS AI", layout="centered")

# ===== STYLE =====
st.markdown("""
<style>
body { background-color: #0d1117; color: white; }
h1 { color: #00ffcc; text-align:center; }
.stButton>button {
    background: linear-gradient(90deg,#00ffcc,#0077ff);
    color:black; border-radius:10px; height:3em; width:100%;
}
</style>
""", unsafe_allow_html=True)

# ===== PAIRS =====
PAIRS = {
    "EUR/USD OTC":"EURUSD=X",
    "GBP/USD OTC":"GBPUSD=X",
    "USD/JPY OTC":"JPY=X",
    "AUD/USD OTC":"AUDUSD=X",
    "USD/CAD OTC":"CAD=X",
    "EUR/JPY OTC":"EURJPY=X",
    "GBP/JPY OTC":"GBPJPY=X"
}

# ===== SESSION =====
def now():
    return datetime.utcnow() + timedelta(hours=1)

def entry_time():
    s = now().second
    return s if s <= 10 else 60 - s

# ===== NOTIFY =====
def notify():
    st.markdown("""
    <script>
    var a=new Audio("https://www.soundjay.com/buttons/sounds/button-3.mp3");
    a.play(); alert("🚨 SIGNAL!");
    </script>
    """, unsafe_allow_html=True)

# ===== DATA =====
def get_data(sym):
    try:
        df = yf.download(sym, interval="1m", period="1d", progress=False)
        if df is None or df.empty or len(df) < 30:
            return None
        df = df[['Open','High','Low','Close']].copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna().reset_index(drop=True)
        return df.tail(50)
    except:
        return None

# ===== INDICATORS =====
def rsi(df):
    d = df["Close"].diff()
    g = d.clip(lower=0).rolling(14).mean()
    l = -d.clip(upper=0).rolling(14).mean()
    rs = g / l
    return (100 - (100/(1+rs))).fillna(50)

def pattern(df):
    if len(df) < 2: return "NONE"
    a, b = df.iloc[-1], df.iloc[-2]
    if b["Close"] < b["Open"] and a["Close"] > a["Open"]: return "BULLISH 📈"
    if b["Close"] > b["Open"] and a["Close"] < a["Open"]: return "BEARISH 📉"
    return "NONE"

# ===== ANALYZE =====
def analyze(sym):
    df = get_data(sym)
    if df is None: return None
    try:
        df["EMA"] = df["Close"].ewm(span=20).mean()
        df["RSI"] = rsi(df)

        c = float(df["Close"].iloc[-1])
        e = float(df["EMA"].iloc[-1])
        r = float(df["RSI"].iloc[-1])

        trend = "UPTREND" if c > e else "DOWNTREND"
        pat = pattern(df)

        return df, trend, pat, r
    except:
        return None

# ===== SIGNAL ENGINE (ULTRA MODE) =====
def best_signal():
    best = None
    best_score = -999

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

        # FORCE DIRECTION
        if call > put:
            direction = "CALL 📈"
        elif put > call:
            direction = "PUT 📉"
        else:
            direction = random.choice(["CALL 📈", "PUT 📉"])

        # SOFT FILTER
        if call < 2 and put < 2:
            call += 1
            put += 1

        score = max(call, put)
        wait = entry_time()

        if score > best_score:
            best = {
                "pair": name,
                "dir": direction,
                "wait": wait,
                "conf": min(99, 75 + score*3)
            }
            best_score = score

    # FORCE SIGNAL ALWAYS
    if best is None:
        pair = random.choice(list(PAIRS.keys()))
        best = {
            "pair": pair,
            "dir": random.choice(["CALL 📈", "PUT 📉"]),
            "wait": entry_time(),
            "conf": random.randint(75, 85)
        }

    return best

# ===== SESSION STATE =====
if "history" not in st.session_state:
    st.session_state.history = []

if "wins" not in st.session_state:
    st.session_state.wins = 0

if "losses" not in st.session_state:
    st.session_state.losses = 0

# ===== UI =====
st.markdown("<h1>💀 FINAL BOSS AI</h1>", unsafe_allow_html=True)

auto = st.toggle("🔄 AUTO MODE", False)

# ===== AUTO =====
if auto:
    box = st.empty()
    while True:
        s = best_signal()
        with box.container():
            notify()
            st.success("🚨 SIGNAL")
            st.write(s)

            st.session_state.history.insert(0, s)
            st.session_state.history = st.session_state.history[:10]

        time.sleep(5)
        st.rerun()

# ===== MANUAL =====
if st.button("🎯 GET SIGNAL"):
    s = best_signal()
    notify()
    st.success("🚨 SIGNAL")
    st.write(s)

    st.session_state.history.insert(0, s)
    st.session_state.history = st.session_state.history[:10]

# ===== TRACK RESULT =====
st.markdown("### 🎯 MARK RESULT")

col1, col2 = st.columns(2)

if col1.button("✅ WIN"):
    st.session_state.wins += 1

if col2.button("❌ LOSS"):
    st.session_state.losses += 1

# ===== DASHBOARD =====
total = st.session_state.wins + st.session_state.losses
acc = (st.session_state.wins / total * 100) if total > 0 else 0

st.markdown("### 📊 PERFORMANCE")
st.write(f"Total Trades: {total}")
st.write(f"Wins: {st.session_state.wins}")
st.write(f"Losses: {st.session_state.losses}")
st.write(f"Accuracy: {round(acc,2)}%")

# ===== HISTORY =====
st.markdown("### 📜 HISTORY")
for h in st.session_state.history:
    st.write(h)
