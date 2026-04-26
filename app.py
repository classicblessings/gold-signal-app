import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests

# ================= SAFE IQ IMPORT =================
try:
    from iqoptionapi.stable_api import IQ_Option
    IQ_AVAILABLE = True
except:
    IQ_AVAILABLE = False

# ================= CONFIG =================
EMAIL = "kholidmusbaudeen1@gmail.com"
PASSWORD = "gbolahan"

BOT_TOKEN = "8654621718"
CHAT_ID = "HardewaleBot"

ASSETS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURJPY"]

TIMEFRAME = 60
MIN_SCORE = 85

# 1–2 MIN INTERVAL CONTROL
MIN_INTERVAL = 60
MAX_INTERVAL = 120

# ================= SESSION STATE =================
if "last_signal_time" not in st.session_state:
    st.session_state.last_signal_time = None

if "last_signal_pair" not in st.session_state:
    st.session_state.last_signal_pair = None

# ================= CONNECT =================
@st.cache_resource
def connect():
    if not IQ_AVAILABLE:
        return None
    try:
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()
        return iq
    except:
        return None

Iq = connect()

# ================= TELEGRAM =================
def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except:
        pass

# ================= DATA =================
def get_data(asset):
    try:
        if IQ_AVAILABLE and Iq:
            candles = Iq.get_candles(asset, TIMEFRAME, 100, time.time())
            df = pd.DataFrame(candles)
            df.rename(columns={"max": "high", "min": "low"}, inplace=True)
            return df

        # fallback demo
        return pd.DataFrame({
            "open": np.random.random(100),
            "high": np.random.random(100),
            "low": np.random.random(100),
            "close": np.random.random(100)
        })

    except:
        return None

# ================= SMART FILTER =================
def smart_filter(df):
    try:
        vol = (df['high'] - df['low']).rolling(10).mean().iloc[-1]
        trend = abs(df['close'].iloc[-1] - df['close'].iloc[-10])

        if vol <= 0:
            return False

        if trend < vol:
            return False

        return True
    except:
        return False

# ================= STRATEGY =================
def generate_signal(df):
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        ma = df['close'].rolling(20).mean().iloc[-1]

        if latest['close'] > ma:
            direction = "BUY"
            score += 25
            reasons.append("Trend Up")
        else:
            direction = "SELL"
            score += 25
            reasons.append("Trend Down")

        if direction == "BUY" and latest['close'] > prev['high']:
            score += 20
            reasons.append("Breakout")

        if direction == "SELL" and latest['close'] < prev['low']:
            score += 20
            reasons.append("Breakout")

        body = abs(latest['close'] - latest['open'])
        rng = latest['high'] - latest['low']

        if rng > 0 and body / rng > 0.6:
            score += 20
            reasons.append("Momentum")

        # liquidity fake breakout
        if latest['high'] > prev['high'] and latest['close'] < prev['high']:
            direction = "SELL"
            score += 25
            reasons.append("Liquidity Grab Sell")

        if latest['low'] < prev['low'] and latest['close'] > prev['low']:
            direction = "BUY"
            score += 25
            reasons.append("Liquidity Grab Buy")

        return direction, score, reasons

    except:
        return None, 0, []

# ================= BEST PAIR =================
def find_best_pair():
    best = None
    best_score = 0

    for asset in ASSETS:
        df = get_data(asset)
        if df is None:
            continue

        if not smart_filter(df):
            continue

        direction, score, reasons = generate_signal(df)

        if direction and score > best_score:
            best = (asset, direction, score, reasons)
            best_score = score

    return best

# ================= SPAM FILTER =================
def can_send_signal(asset):
    now = datetime.now()

    if st.session_state.last_signal_time is None:
        return True

    diff = (now - st.session_state.last_signal_time).seconds

    # enforce 1–2 min gap
    if diff < MIN_INTERVAL:
        return False

    # avoid same pair repeatedly
    if asset == st.session_state.last_signal_pair and diff < MAX_INTERVAL:
        return False

    return True

def update_signal(asset):
    st.session_state.last_signal_time = datetime.now()
    st.session_state.last_signal_pair = asset

# ================= UI =================
st.set_page_config(layout="centered")

st.markdown("""
<style>
body {background:#0e1117;color:white;}
.card {
    background:#111827;
    padding:20px;
    border-radius:20px;
    text-align:center;
    margin-bottom:15px;
}
.big {font-size:28px;font-weight:bold;}
.green {color:#00ff99;}
</style>
""", unsafe_allow_html=True)

st.title("📡 Signal Radar PRO")

# STATUS
if IQ_AVAILABLE:
    st.success("🟢 Live Mode")
else:
    st.warning("⚠️ Demo Mode")

# ================= SCAN BUTTON =================
if st.button("🔍 Scan Market"):

    best = find_best_pair()

    if not best:
        st.warning("No valid setup found")
    else:
        asset, direction, score, reasons = best

        if score < MIN_SCORE:
            st.warning("No strong signal")
        else:
            if not can_send_signal(asset):
                st.warning("⏳ Waiting interval (anti-spam active)")
            else:
                update_signal(asset)

                # UI
                st.markdown(f"""
                <div class="card">
                <div class="big">{direction}</div>
                <div>{asset}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="card">
                <div>Confidence</div>
                <div class="green big">{score}%</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 🧠 Breakdown")
                for r in reasons:
                    st.write(f"✔ {r}")

                msg = f"""
🚀 SIGNAL

Pair: {asset}
Direction: {direction}
Confidence: {score}%

🧠 {' | '.join(reasons)}
"""
                send_telegram(msg)

# ================= AUTO REFRESH =================
st.caption("Auto refresh every 20 seconds")
time.sleep(20)
st.rerun()
