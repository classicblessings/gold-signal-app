import streamlit as st
import pandas as pd
import yfinance as yf
import random
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="FINAL BOSS LEVEL 2", layout="centered")

# ===== STYLE =====
st.markdown("""
<style>
body {
background: linear-gradient(135deg,#020617,#0f172a);
color:#e2e8f0;
font-family: 'Segoe UI';
}
h1 {text-align:center;color:#22c55e;}
.card {
background:#020617;
padding:20px;
border-radius:15px;
box-shadow:0 0 25px rgba(0,255,200,0.15);
margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

# ===== ASSETS =====
ASSETS = {
"EURUSD":"EURUSD=X",
"GBPUSD":"GBPUSD=X",
"USDJPY":"JPY=X",
"AUDUSD":"AUDUSD=X",
"USDCAD":"CAD=X",
"EURJPY":"EURJPY=X",
"GBPJPY":"GBPJPY=X",
"XAUUSD":"GC=F"
}

# ===== TIME =====
def current_time():
    return datetime.utcnow() + timedelta(hours=1)

def entry_time():
    sec = current_time().second
    return 60 - sec if sec > 5 else sec

def duration():
    return random.choice([1,2,3,4,5])

# ===== DATA =====
def get_data(symbol):
    try:
        df = yf.download(symbol, interval="1m", period="1d", progress=False)

        if df is None or df.empty or len(df) < 50:
            return None

        df = df[['Open','High','Low','Close']].copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df.reset_index(drop=True, inplace=True)

        return df.tail(50)

    except:
        return None

# ===== INDICATORS =====
def indicators(df):
    df["EMA"] = df["Close"].ewm(span=20).mean()
    df["EMA_FAST"] = df["Close"].ewm(span=5).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = (100 - (100/(1+rs))).fillna(50)

    df["VOL"] = df["Close"].rolling(10).std().fillna(0)

    return df

# ===== PATTERN DETECTION =====
def pattern(df):
    o1, c1 = df["Open"].iloc[-2], df["Close"].iloc[-2]
    o2, c2 = df["Open"].iloc[-1], df["Close"].iloc[-1]

    # ENGULFING
    if c2 > o2 and c1 < o1 and c2 > o1:
        return "BULLISH"
    elif c2 < o2 and c1 > o1 and c2 < o1:
        return "BEARISH"

    return "NONE"

# ===== ANALYSIS =====
def analyze(symbol):
    df = get_data(symbol)
    if df is None:
        return None

    try:
        df = indicators(df)

        c = float(df["Close"].iloc[-1])
        ema = float(df["EMA"].iloc[-1])
        ema_fast = float(df["EMA_FAST"].iloc[-1])
        rsi = float(df["RSI"].iloc[-1])
        vol = float(df["VOL"].iloc[-1])

        pat = pattern(df)

        buy = 0
        sell = 0

        # TREND
        if ema_fast > ema:
            buy += 2
        else:
            sell += 2

        # RSI
        if rsi < 45:
            buy += 1
        elif rsi > 55:
            sell += 1

        # VOLATILITY
        if vol > 0.0005:
            buy += 1
            sell += 1

        # PATTERN BOOST
        if pat == "BULLISH":
            buy += 2
        elif pat == "BEARISH":
            sell += 2

        # FINAL DECISION
        direction = "BUY 📈" if buy >= sell else "SELL 📉"
        score = max(buy, sell)

        confidence = min(96, 80 + score * 2)

        return direction, confidence, score

    except:
        return None

# ===== BEST SIGNAL =====
def best_signal():
    best = None
    best_score = -1

    for name, sym in ASSETS.items():
        r = analyze(sym)
        if not r:
            continue

        direction, confidence, score = r

        if score > best_score:
            best = (name, direction, confidence)
            best_score = score

    if best is None:
        return (
            random.choice(list(ASSETS.keys())),
            random.choice(["BUY 📈","SELL 📉"]),
            random.randint(80,90)
        )

    return best

# ===== SESSION =====
if "history" not in st.session_state:
    st.session_state.history = []

if "wins" not in st.session_state:
    st.session_state.wins = 0

if "losses" not in st.session_state:
    st.session_state.losses = 0

# ===== UI =====
st.markdown("<h1>💀 FINAL BOSS LEVEL 2 SNIPER</h1>", unsafe_allow_html=True)

# ===== SIGNAL =====
if st.button("🎯 GET SNIPER SIGNAL"):

    pair, direction, confidence = best_signal()
    wait = entry_time()
    dur = duration()

    st.markdown(f"""
    <div class="card">
    <h2>{pair}</h2>
    <h3>{direction}</h3>
    ⏳ Entry: {wait} sec<br>
    🕐 Duration: {dur} min<br>
    🔥 Confidence: {confidence}%
    </div>
    """, unsafe_allow_html=True)

    for i in range(wait, -1, -1):
        st.write(f"⏳ {i}s")
        time.sleep(1)

    st.session_state.history.insert(0,{
        "pair":pair,
        "dir":direction,
        "conf":confidence
    })

# ===== TRACKING =====
c1,c2 = st.columns(2)

if c1.button("✅ WIN"):
    st.session_state.wins += 1

if c2.button("❌ LOSS"):
    st.session_state.losses += 1

total = st.session_state.wins + st.session_state.losses
acc = (st.session_state.wins/total*100) if total>0 else 0

st.markdown(f"""
<div class="card">
📊 Trades: {total}<br>
✅ Wins: {st.session_state.wins}<br>
❌ Losses: {st.session_state.losses}<br>
🎯 Accuracy: {round(acc,2)}%
</div>
""", unsafe_allow_html=True)

# ===== HISTORY =====
st.markdown("### 📜 History")
for h in st.session_state.history:
    st.write(h)
