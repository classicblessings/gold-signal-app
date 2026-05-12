# Marathon Signal Radar PRO — Single File Streamlit App

Save this as `app.py`

```python
import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import requests

# ================= CONFIG =================
EMAIL = "YOUR_EMAIL"
PASSWORD = "YOUR_PASSWORD"
BOT_TOKEN = "YOUR_TELEGRAM_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"
NEWS_API_KEY = "YOUR_NEWS_API_KEY"

# NON-OTC FOREX PAIRS ONLY
ASSETS = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "EURJPY",
    "GBPJPY",
    "USDCAD"
]

TIMEFRAME = 60
MIN_SCORE = 85
SIGNAL_INTERVAL = 60

# ================= PAGE =================
st.set_page_config(
    page_title="Marathon Signal Radar PRO",
    page_icon="📡",
    layout="centered"
)

# ================= SESSION STATE =================
if "last_signal" not in st.session_state:
    st.session_state.last_signal = None

if "last_signal_time" not in st.session_state:
    st.session_state.last_signal_time = None

# ================= CSS UI =================
st.markdown("""
<style>

html, body, [class*="css"] {
    background: linear-gradient(180deg, #1e3a8a 0%, #7c3aed 100%);
    color: white;
    font-family: 'Segoe UI';
}

.main {
    padding-top: 0rem;
}

.block-container {
    padding-top: 1rem;
}

.topbar {
    background: rgba(255,255,255,0.15);
    border-radius: 18px;
    padding: 14px;
    margin-bottom: 18px;
    text-align: center;
    backdrop-filter: blur(10px);
}

.radar {
    width: 280px;
    height: 280px;
    border-radius: 50%;
    margin: auto;
    margin-top: 12px;

    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;

    background:
    radial-gradient(circle at center,
    #06b6d4 10%,
    #8b5cf6 55%,
    #ec4899 100%);

    box-shadow:
    0 0 20px rgba(255,255,255,0.35),
    0 0 40px rgba(236,72,153,0.45),
    0 0 70px rgba(6,182,212,0.45);

    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% {transform: scale(1);}
    50% {transform: scale(1.02);}
    100% {transform: scale(1);}
}

.signal {
    font-size: 42px;
    font-weight: 800;
}

.pair {
    font-size: 20px;
    margin-bottom: 6px;
}

.conf {
    font-size: 18px;
    margin-top: 6px;
}

.card {
    background: rgba(255,255,255,0.15);
    border-radius: 22px;
    padding: 16px;
    margin-top: 16px;
    backdrop-filter: blur(10px);
}

.status {
    text-align:center;
    font-size:15px;
    font-weight:600;
}

.countdown {
    font-size:32px;
    font-weight:800;
    text-align:center;
}

.reason {
    background: rgba(255,255,255,0.12);
    padding: 10px;
    border-radius: 12px;
    margin-top: 8px;
}

</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown("""
<div class="topbar">
<h2>📡 Marathon Signal Radar PRO</h2>
<div class="status">
🟢 LIVE FOREX SCANNER ACTIVE • NON-OTC • 1M BLITZ
</div>
</div>
""", unsafe_allow_html=True)

# ================= IQ OPTION =================
@st.cache_resource
def connect_iq():
    try:
        from iqoptionapi.stable_api import IQ_Option
        iq = IQ_Option(EMAIL, PASSWORD)
        iq.connect()
        return iq
    except:
        return None

IQ = connect_iq()

# ================= TELEGRAM =================
def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=5
        )
    except:
        pass

# ================= NEWS FILTER =================
def high_news_detected():
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines?"
            f"category=business&apiKey={NEWS_API_KEY}"
        )

        response = requests.get(url, timeout=5).json()

        keywords = [
            "interest rate",
            "inflation",
            "cpi",
            "fomc",
            "nfp",
            "gdp"
        ]

        for article in response.get("articles", [])[:10]:
            title = article.get("title", "").lower()

            if any(word in title for word in keywords):
                return True

        return False

    except:
        return False

# ================= DATA =================
def get_data(asset):
    try:
        if IQ is None:
            return None

        candles = IQ.get_candles(asset, TIMEFRAME, 120, time.time())

        if candles is None:
            return None

        df = pd.DataFrame(candles)

        if len(df) < 30:
            return None

        df.rename(columns={
            "max": "high",
            "min": "low"
        }, inplace=True)

        return df

    except:
        return None

# ================= FILTERS =================
def strong_trend(df):
    try:
        trend = abs(df['close'].iloc[-1] - df['close'].iloc[-10])
        volatility = (
            df['high'] - df['low']
        ).rolling(10).mean().iloc[-1]

        return trend > volatility
    except:
        return False


def candle_quality(df):
    try:
        latest = df.iloc[-1]

        body = abs(latest['close'] - latest['open'])
        candle_range = latest['high'] - latest['low']

        if candle_range <= 0:
            return False

        strength = body / candle_range

        # avoid weak balance candles
        return strength > 0.62

    except:
        return False

# ================= STRATEGY =================
def generate_signal(df):
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        score = 0
        reasons = []

        ma20 = df['close'].rolling(20).mean().iloc[-1]

        # TREND
        if latest['close'] > ma20:
            direction = "BUY"
            score += 30
            reasons.append("Strong Uptrend")
        else:
            direction = "SELL"
            score += 30
            reasons.append("Strong Downtrend")

        # BREAKOUT
        if direction == "BUY":
            if latest['close'] > prev['high']:
                score += 25
                reasons.append("Bullish Breakout")

        if direction == "SELL":
            if latest['close'] < prev['low']:
                score += 25
                reasons.append("Bearish Breakout")

        # MOMENTUM
        if candle_quality(df):
            score += 20
            reasons.append("Strong Momentum Candle")

        # VOLUME STYLE PRESSURE
        candle_body = abs(latest['close'] - latest['open'])
        candle_range = latest['high'] - latest['low']

        if candle_range > 0:
            ratio = candle_body / candle_range

            if ratio > 0.75:
                score += 15
                reasons.append("High Directional Pressure")

        return direction, score, reasons

    except:
        return None, 0, []

# ================= CONFIRM =================
def confirm_signal(df, direction):
    try:
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if direction == "BUY":
            return latest['close'] > prev['high']

        if direction == "SELL":
            return latest['close'] < prev['low']

        return False

    except:
        return False

# ================= COUNTDOWN =================
def countdown_seconds():
    return 60 - datetime.now().second

# ================= ENTRY TIME =================
def next_entry_time():
    now = datetime.now()

    nxt = now.replace(second=0, microsecond=0)

    if now.second > 0:
        nxt += timedelta(minutes=1)

    return nxt.strftime("%H:%M:%S")

# ================= COOLDOWN =================
def can_generate_new_signal():
    if st.session_state.last_signal_time is None:
        return True

    elapsed = (
        datetime.now() - st.session_state.last_signal_time
    ).seconds

    return elapsed >= SIGNAL_INTERVAL

# ================= LIVE SCAN =================
def scan_market():

    if high_news_detected():
        return None

    best_signal = None
    best_score = 0

    for asset in ASSETS:

        df = get_data(asset)

        if df is None:
            continue

        if not strong_trend(df):
            continue

        if not candle_quality(df):
            continue

        direction, score, reasons = generate_signal(df)

        if direction is None:
            continue

        if score < MIN_SCORE:
            continue

        if not confirm_signal(df, direction):
            continue

        if score > best_score:
            best_signal = {
                "asset": asset,
                "direction": direction,
                "score": score,
                "reasons": reasons,
                "entry": next_entry_time()
            }
            best_score = score

    return best_signal

# ================= AUTO SIGNAL =================
if can_generate_new_signal():

    signal = scan_market()

    if signal:

        st.session_state.last_signal = signal
        st.session_state.last_signal_time = datetime.now()

        telegram_message = f"""
🚀 STRONG FOREX SIGNAL

Pair: {signal['asset']}
Market: NON-OTC
Mode: 1M BLITZ

Direction: {signal['direction']}
Confidence: {signal['score']}%

⏰ Entry: {signal['entry']}

🧠 {' | '.join(signal['reasons'])}
"""

        send_telegram(telegram_message)

# ================= SHOW SIGNAL =================
if st.session_state.last_signal:

    signal = st.session_state.last_signal

    st.markdown(f"""
    <div class="radar">
        <div class="pair">{signal['asset']}</div>
        <div class="signal">{signal['direction']}</div>
        <div class="conf">{signal['score']}% CONFIDENCE</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
    <div class="countdown">
    ⏳ {countdown_seconds()}s
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
    ⏰ ENTRY TIME: <b>{signal['entry']}</b><br><br>
    📊 TYPE: NON-OTC FOREX<br>
    ⚡ MODE: 1M BLITZ
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🧠 Signal Breakdown")

    for reason in signal['reasons']:
        st.markdown(
            f"<div class='reason'>✔ {reason}</div>",
            unsafe_allow_html=True
        )

    # 5 SEC ALERT
    if countdown_seconds() <= 5:
        st.audio(
            "https://www.soundjay.com/buttons/beep-07.wav"
        )

else:

    st.markdown("""
    <div class="card">
    🔍 Scanning live market for strong setups...<br><br>
    Waiting for clean breakout + momentum confirmation.
    </div>
    """, unsafe_allow_html=True)

# ================= CONNECTION STATUS =================
if IQ is None:
    st.error("❌ IQ Option connection failed")
else:
    st.success("🟢 Connected to Live Market")

# ================= LIVE REFRESH =================
time.sleep(10)
st.rerun()
```

## Install Requirements

```bash
pip install streamlit pandas numpy requests iqoptionapi
```

## Run App

```bash
streamlit run app.py
```
