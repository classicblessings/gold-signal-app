import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

st.set_page_config(page_title="FINAL BOSS AUTO SNIPER", layout="centered")

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
margin-top:10px;
box-shadow:0 0 20px rgba(0,255,200,0.1);
}
</style>
""", unsafe_allow_html=True)

# ===== ASSETS =====
ASSETS = {
"EURUSD":"EURUSD=X",
"GBPUSD":"GBPUSD=X",
"USDJPY":"JPY=X",
"AUDUSD":"AUDUSD=X",
"EURJPY":"EURJPY=X",
"GBPJPY":"GBPJPY=X",
"XAUUSD":"GC=F"
}

# ===== TIME =====
def entry_time():
    sec = datetime.utcnow().second
    return 60 - sec if sec > 5 else sec

# ===== DATA =====
def get_data(sym):
    try:
        df = yf.download(sym, interval="1m", period="1d", progress=False)

        if df is None or df.empty or len(df) < 60:
            return None

        df = df[['Open','High','Low','Close']].copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df.reset_index(drop=True, inplace=True)

        return df.tail(60)

    except:
        return None

# ===== INDICATORS =====
def indicators(df):
    df["EMA_FAST"] = df["Close"].ewm(span=5).mean()
    df["EMA_SLOW"] = df["Close"].ewm(span=20).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = (100 - (100/(1+rs))).fillna(50)

    df["VOL"] = df["Close"].rolling(10).std().fillna(0)

    return df

# ===== PATTERN =====
def pattern(df):
    o1,c1 = df["Open"].iloc[-2], df["Close"].iloc[-2]
    o2,c2 = df["Open"].iloc[-1], df["Close"].iloc[-1]

    if c2 > o2 and c1 < o1 and c2 > o1:
        return "Bullish Engulfing"
    elif c2 < o2 and c1 > o1 and c2 < o1:
        return "Bearish Engulfing"
    return "None"

# ===== ANALYSIS =====
def analyze(sym):
    df = get_data(sym)
    if df is None:
        return None

    df = indicators(df)

    ema_fast = df["EMA_FAST"].iloc[-1]
    ema_slow = df["EMA_SLOW"].iloc[-1]
    rsi = df["RSI"].iloc[-1]
    vol = df["VOL"].iloc[-1]
    pat = pattern(df)

    # ===== FILTER (IMPORTANT) =====
    if vol < 0.0003:
        return None  # skip weak market

    score = 0
    reasons = []

    # TREND
    if ema_fast > ema_slow:
        direction = "BUY 📈"
        score += 2
        reasons.append("Uptrend")
    else:
        direction = "SELL 📉"
        score += 2
        reasons.append("Downtrend")

    # RSI
    if rsi < 45:
        score += 1
        reasons.append("Oversold")
    elif rsi > 55:
        score += 1
        reasons.append("Overbought")

    # PATTERN BOOST
    if pat != "None":
        score += 2
        reasons.append(pat)

    confidence = min(92, 80 + score * 2)

    return direction, confidence, reasons

# ===== AUTO SIGNAL =====
def get_signal():
    best = None
    best_score = 0

    for name, sym in ASSETS.items():
        result = analyze(sym)
        if not result:
            continue

        direction, confidence, reasons = result

        if confidence > best_score:
            best = (name, direction, confidence, reasons)
            best_score = confidence

    return best

# ===== UI =====
st.markdown("<h1>💀 FINAL BOSS AUTO SNIPER</h1>", unsafe_allow_html=True)

if st.button("🎯 GET STRONG SIGNAL"):

    signal = get_signal()

    if signal is None:
        st.warning("⚠️ Market not good — WAIT (this protects your money)")
    else:
        pair, direction, confidence, reasons = signal
        wait = entry_time()

        st.markdown(f"""
        <div class="card">
        <h2>{pair}</h2>
        <h3>{direction}</h3>
        ⏳ Entry: {wait}s<br>
        🔥 Confidence: {confidence}%<br>
        📊 Reason: {", ".join(reasons)}
        </div>
        """, unsafe_allow_html=True)

        for i in range(wait, -1, -1):
            st.write(f"⏳ {i}s")
            time.sleep(1)

        st.success("👉 Enter trade NOW (1 minute)")
