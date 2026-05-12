import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests

# ================= CONFIG =================
EMAIL = "classicblessings2025@gmail.com"
PASSWORD = "hardewale"
BOT_TOKEN = "8654621718"
CHAT_ID = "HardewaleBot"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

ASSETS = ["EURUSD","GBPUSD","USDJPY","AUDUSD","EURJPY"]

TIMEFRAME = 60
MIN_SCORE = 85

# ================= STATE =================
if "last_signal" not in st.session_state:
    st.session_state.last_signal = None

if "last_time" not in st.session_state:
    st.session_state.last_time = None

# ================= SESSION =================
def session_active():
    hour = datetime.now().hour
    return (8 <= hour < 11) or (13 <= hour < 16)

# ================= IQ =================
try:
    from iqoptionapi.stable_api import IQ_Option
    iq = IQ_Option(EMAIL, PASSWORD)
    iq.connect()
    CONNECTED = True
except:
    CONNECTED = False

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass

# ================= NEWS FILTER =================
def high_impact_news():
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={NEWS_API_KEY}"
        res = requests.get(url, timeout=5).json()

        keywords = ["interest rate","inflation","cpi","fomc","nfp","gdp"]

        for a in res.get("articles", [])[:10]:
            title = a["title"].lower()
            if any(k in title for k in keywords):
                return True
        return False
    except:
        return False

# ================= DATA =================
def get_data(asset):
    try:
        candles = iq.get_candles(asset, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)
        df.rename(columns={"max":"high","min":"low"}, inplace=True)
        return df
    except:
        return None

# ================= FILTER =================
def smart_filter(df):
    vol = (df['high'] - df['low']).rolling(10).mean().iloc[-1]
    trend = abs(df['close'].iloc[-1] - df['close'].iloc[-10])
    return trend > vol

def candle_quality(df):
    latest = df.iloc[-1]
    body = abs(latest['close'] - latest['open'])
    rng = latest['high'] - latest['low']

    # reject weak/balanced candles
    if rng == 0:
        return False

    strength = body / rng

    # ONLY strong directional candles
    return strength > 0.6

# ================= STRATEGY =================
def generate_signal(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0
    reasons = []

    ma = df['close'].rolling(20).mean().iloc[-1]

    if latest['close'] > ma:
        direction = "BUY"
        score += 30
        reasons.append("Trend Up")
    else:
        direction = "SELL"
        score += 30
        reasons.append("Trend Down")

    if direction == "BUY" and latest['close'] > prev['high']:
        score += 25
        reasons.append("Breakout")

    if direction == "SELL" and latest['close'] < prev['low']:
        score += 25
        reasons.append("Breakout")

    if candle_quality(df):
        score += 20
        reasons.append("Strong Candle")

    return direction, score, reasons

# ================= CONFIRM =================
def confirm(df, direction):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    if direction == "BUY" and latest['close'] < prev['high']:
        return False
    if direction == "SELL" and latest['close'] > prev['low']:
        return False

    return True

# ================= COOLDOWN =================
def cooldown():
    if st.session_state.last_time is None:
        return False
    return (datetime.now() - st.session_state.last_time).seconds < 120

# ================= ENTRY =================
def get_entry():
    now = datetime.now()
    nxt = now.replace(second=0, microsecond=0)
    if now.second > 0:
        nxt += timedelta(minutes=1)
    return nxt

def countdown():
    return 60 - datetime.now().second

# ================= UI =================
st.set_page_config(layout="centered")

st.markdown("""
<style>
body {background:#0e1117;color:white;text-align:center;}
.radar {
width:220px;height:220px;border-radius:50%;
margin:auto;display:flex;flex-direction:column;
justify-content:center;align-items:center;
background: radial-gradient(circle, #1f2937 40%, #00ff99 100%);
box-shadow:0 0 25px #00ff99;
}
.big {font-size:26px;font-weight:bold;}
.small {font-size:14px;color:#ccc;}
</style>
""", unsafe_allow_html=True)

st.title("📡 Smart Signal Radar PRO")

# ================= SHOW LAST SIGNAL =================
if st.session_state.last_signal:
    st.info("Last Signal Active")

    sig = st.session_state.last_signal
    cd = countdown()

    st.markdown(f"""
    <div class="radar">
        <div class="small">{sig['asset']}</div>
        <div class="big">{sig['direction']}</div>
        <div class="small">{sig['score']}%</div>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"⏰ Entry: {sig['entry']}")
    st.write(f"⏳ Countdown: {cd}s")

    # 🔊 5 SECOND ALERT
    if cd <= 5:
        st.audio("https://www.soundjay.com/buttons/beep-07.wav")

# ================= BUTTON =================
if st.button("GET SIGNAL"):

    if not session_active():
        st.warning("Outside session")
        st.stop()

    if cooldown():
        st.warning("Wait 2 min")
        st.stop()

    if high_impact_news():
        st.error("High impact news — skip")
        st.stop()

    best = None
    best_score = 0

    for asset in ASSETS:
        df = get_data(asset)
        if df is None:
            continue

        if not smart_filter(df):
            continue

        direction, score, reasons = generate_signal(df)

        if score > best_score:
            best = (asset, direction, score, reasons)
            best_score = score

    if not best:
        st.warning("No clean setup")
        st.stop()

    asset, direction, score, reasons = best

    st.info("Reconfirming...")
    time.sleep(5)

    df = get_data(asset)

    if not confirm(df, direction):
        st.warning("Fake breakout")
        st.stop()

    entry = get_entry().strftime("%H:%M:%S")

    st.session_state.last_signal = {
        "asset": asset,
        "direction": direction,
        "score": score,
        "entry": entry
    }

    st.session_state.last_time = datetime.now()

    msg = f"""
🚀 STRONG SIGNAL

Pair: {asset}
Type: NON-OTC
Mode: 1M BLITZ

Direction: {direction}
Confidence: {score}%

⏰ Entry: {entry}
"""
    send_telegram(msg)
