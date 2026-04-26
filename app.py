import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests

from iqoptionapi.stable_api import IQ_Option

# ================= CONFIG =================
EMAIL = "kholidmusbaudeen@gmail.com"
PASSWORD = "gbolahan"

BOT_TOKEN = "8654621718"
CHAT_ID = "HardewaleBot"

ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY", "GBPJPY"]

TIMEFRAME = 60
MIN_SCORE = 85
COOLDOWN = 120

last_signal_time = None

# ================= CONNECT =================
@st.cache_resource
def connect():
    try:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()
        return iq
    except Exception as e:
        st.error(f"IQ Option connection failed: {e}")
        return None

Iq = connect()

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

# ================= SESSION =================
def session_filter():
    hour = datetime.now().hour
    return (8 <= hour < 11) or (13 <= hour < 16)

# ================= COOLDOWN =================
def can_send_signal():
    global last_signal_time
    if last_signal_time is None:
        return True
    return (datetime.now() - last_signal_time).seconds >= COOLDOWN

def update_time():
    global last_signal_time
    last_signal_time = datetime.now()

# ================= DATA =================
def get_data(asset):
    try:
        candles = Iq.get_candles(asset, TIMEFRAME, 100, time.time())
        df = pd.DataFrame(candles)

        if df.empty or len(df) < 50:
            return None

        df.rename(columns={"max": "high", "min": "low"}, inplace=True)
        return df

    except Exception as e:
        print(f"Data error {asset}:", e)
        return None

# ================= STRATEGY =================
def generate_signal(df):

    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        # TREND
        ma = df['close'].rolling(20).mean().iloc[-1]
        if latest['close'] > ma:
            direction = "BUY"
            score += 25
            reasons.append("Trend Up")
        else:
            direction = "SELL"
            score += 25
            reasons.append("Trend Down")

        # BREAKOUT
        if direction == "BUY" and latest['close'] > prev['high']:
            score += 20
            reasons.append("Breakout")

        if direction == "SELL" and latest['close'] < prev['low']:
            score += 20
            reasons.append("Breakout")

        # MOMENTUM
        body = abs(latest['close'] - latest['open'])
        rng = latest['high'] - latest['low']

        if rng > 0 and body / rng > 0.6:
            score += 20
            reasons.append("Strong Candle")

        # LIQUIDITY SWEEP
        if latest['high'] > prev['high'] and latest['close'] < prev['high']:
            direction = "SELL"
            score += 25
            reasons.append("Liquidity Grab Sell")

        if latest['low'] < prev['low'] and latest['close'] > prev['low']:
            direction = "BUY"
            score += 25
            reasons.append("Liquidity Grab Buy")

        return direction, score, reasons

    except Exception as e:
        print("Strategy error:", e)
        return None, 0, []

# ================= BEST PAIR DETECTION =================
def find_best_pair():

    best = None
    best_score = 0

    for asset in ASSETS:

        df = get_data(asset)
        if df is None:
            continue

        direction, score, reasons = generate_signal(df)

        if direction and score > best_score:
            best = (asset, direction, score, reasons)
            best_score = score

    return best

# ================= ENTRY TIME =================
def get_entry_time():
    now = datetime.now()
    next_candle = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    return next_candle.strftime("%H:%M:%S")

# ================= UI =================
st.set_page_config(layout="centered")

st.markdown("""
<style>
body {background-color:#0e1117;color:white;}
.card {
    background:#111827;
    padding:20px;
    border-radius:20px;
    text-align:center;
    margin-bottom:15px;
    box-shadow:0px 0px 15px rgba(0,255,150,0.2);
}
.big {font-size:28px;font-weight:bold;}
.green {color:#00ff99;}
.small {color:#9ca3af;}
</style>
""", unsafe_allow_html=True)

st.title("📡 Signal Radar PRO")

# STATUS
if session_filter():
    st.success("🟢 Session Active (8–11 AM / 1–4 PM)")
else:
    st.error("🔴 Outside Trading Session")

# ================= MAIN =================
if st.button("🔍 Scan Best Pair"):

    if Iq is None:
        st.error("IQ Option not connected")
        st.stop()

    if not session_filter():
        st.warning("Outside session")
        st.stop()

    if not can_send_signal():
        st.warning("⏳ Wait 2 minutes interval")
        st.stop()

    best_signal = find_best_pair()

    if best_signal:

        asset, direction, score, reasons = best_signal

        if score < MIN_SCORE:
            st.warning("No strong pair found")
            st.stop()

        entry_time = get_entry_time()

        # UI
        st.markdown(f"""
        <div class="card">
        <div class="big">{direction}</div>
        <div>{asset}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
        <div>AI Confidence</div>
        <div class="green big">{score}%</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
        <div>Entry Time</div>
        <div class="big">{entry_time}</div>
        <div class="small">Enter within 0–10 sec</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🧠 Confidence Breakdown")
        for r in reasons:
            st.write(f"✔ {r}")

        msg = f"""
🚀 BEST SIGNAL

Pair: {asset}
Direction: {direction}
Strength: {score}%

⏰ Entry: {entry_time}
🧠 {' | '.join(reasons)}
"""

        send_telegram(msg)
        update_time()

    else:
        st.warning("No valid signals across all pairs")
