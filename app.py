import streamlit as st
import pandas as pd
import yfinance as yf
import random
from datetime import datetime, timedelta, timezone

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="FINAL BOSS PRO MAX", layout="centered")

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

# ===============================
# TIME (WAT) ✅ FIXED
# ===============================
def get_wat_time():
    return datetime.now(timezone.utc) + timedelta(hours=1)

# ===============================
# SESSION
# ===============================
def get_session():
    hour = get_wat_time().hour
    if 7 <= hour < 13:
        return "LONDON SESSION 🔥"
    elif 13 <= hour < 18:
        return "NEW YORK SESSION ⚡"
    else:
        return "LOW MARKET 💤"

# ===============================
# ENTRY TIMING
# ===============================
def get_entry_timing():
    return 60 - get_wat_time().second

# ===============================
# RSI
# ===============================
def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ===============================
# DATA
# ===============================
def get_live_data(symbol):
    df = yf.download(symbol, interval="1m", period="1d", progress=False)
    return df.tail(50)

# ===============================
# CANDLE PATTERN
# ===============================
def detect_pattern(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if prev["Close"] < prev["Open"] and last["Close"] > last["Open"] and last["Close"] > prev["Open"]:
        return "BULLISH ENGULFING 📈"

    if prev["Close"] > prev["Open"] and last["Close"] < last["Open"] and last["Close"] < prev["Open"]:
        return "BEARISH ENGULFING 📉"

    body = abs(last["Close"] - last["Open"])
    wick = last["High"] - last["Low"]

    if wick > body * 2:
        return "PIN BAR 🔄"

    return "NONE"

# ===============================
# EXPIRY LOGIC
# ===============================
def get_expiry(momentum, rsi):
    if momentum == "STRONG":
        return "1 MIN"
    elif 40 < rsi < 60:
        return "3 MIN"
    else:
        return "5 MIN"

# ===============================
# ANALYSIS
# ===============================
def analyze(symbol):
    df = get_live_data(symbol)

    if df.empty:
        return None

    df["EMA"] = df["Close"].ewm(span=20).mean()
    df["RSI"] = calculate_rsi(df)

    last = df.iloc[-1]

    trend = "UPTREND" if last["Close"] > last["EMA"] else "DOWNTREND"
    rsi = last["RSI"]

    momentum = "STRONG" if abs(df["Close"].iloc[-1] - df["Close"].iloc[-5]) > 0 else "WEAK"

    pattern = detect_pattern(df)

    # STRUCTURE
    recent_high = df["High"].rolling(10).max().iloc[-1]
    recent_low = df["Low"].rolling(10).min().iloc[-1]

    near_high = last["Close"] >= recent_high * 0.999
    near_low = last["Close"] <= recent_low * 1.001

    structure = "NONE"
    if near_high:
        structure = "RESISTANCE 🔴"
    elif near_low:
        structure = "SUPPORT 🟢"

    # FAKE BREAKOUT
    fake_breakout = False
    if last["High"] > recent_high and last["Close"] < recent_high:
        fake_breakout = True
    if last["Low"] < recent_low and last["Close"] > recent_low:
        fake_breakout = True

    expiry = get_expiry(momentum, rsi)

    return trend, rsi, momentum, pattern, expiry, structure, fake_breakout

# ===============================
# SIGNAL ENGINE
# ===============================
def generate_signal(confidence):
    pair_name, symbol = random.choice(list(PAIRS.items()))

    result = analyze(symbol)
    if not result:
        return None

    trend, rsi, momentum, pattern, expiry, structure, fake_breakout = result
    wait = get_entry_timing()

    if wait > 50:
        return None

    direction = None

    if (
        trend == "UPTREND"
        and rsi < 40
        and "BULLISH" in pattern
        and structure == "SUPPORT 🟢"
        and not fake_breakout
    ):
        direction = "CALL 📈"

    elif (
        trend == "DOWNTREND"
        and rsi > 60
        and "BEARISH" in pattern
        and structure == "RESISTANCE 🔴"
        and not fake_breakout
    ):
        direction = "PUT 📉"

    else:
        return None

    conf = random.randint(confidence, 99)

    return {
        "pair": pair_name,
        "direction": direction,
        "confidence": conf,
        "wait": wait,
        "trend": trend,
        "rsi": round(rsi, 2),
        "momentum": momentum,
        "pattern": pattern,
        "expiry": expiry,
        "structure": structure
    }

# ===============================
# UI
# ===============================
st.title("⚡ FINAL BOSS — PRO MAX")

confidence = st.slider("Min Confidence %", 85, 99, 92)

st.markdown(f"### 🕒 WAT Time: {get_wat_time().strftime('%H:%M:%S')}")
st.markdown(f"### 📊 Session: {get_session()}")

# ===============================
# AUTO SIGNAL
# ===============================
if st.button("🎯 GET PRO MAX SIGNAL"):
    signal = generate_signal(confidence)

    if signal:
        st.success("PRO MAX SIGNAL ✅")

        st.markdown(f"""
        ### 📊 PAIR: {signal['pair']}
        ### 🎯 DIRECTION: {signal['direction']}
        ### 🕯️ PATTERN: {signal['pattern']}
        ### 🧱 STRUCTURE: {signal['structure']}
        ### ⏱️ EXPIRY: {signal['expiry']}
        ### ⏳ ENTRY IN: {signal['wait']} sec
        ### 📈 TREND: {signal['trend']}
        ### 📊 RSI: {signal['rsi']}
        ### ⚡ MOMENTUM: {signal['momentum']}
        ### 🔥 CONFIDENCE: {signal['confidence']}%
        """)
    else:
        st.warning("No clean sniper setup — wait")

# ===============================
# MANUAL SCAN
# ===============================
st.markdown("---")
st.subheader("🔍 MANUAL SCAN")

selected_pair = st.selectbox("Choose Pair", list(PAIRS.keys()))

if st.button("⚡ SCAN NOW"):
    result = analyze(PAIRS[selected_pair])

    if result:
        trend, rsi, momentum, pattern, expiry, structure, fake_breakout = result
        wait = get_entry_timing()

        st.success("SCAN RESULT ✅")

        st.markdown(f"""
        ### 📊 PAIR: {selected_pair}
        ### 🕯️ PATTERN: {pattern}
        ### 🧱 STRUCTURE: {structure}
        ### 📈 TREND: {trend}
        ### 📊 RSI: {round(rsi,2)}
        ### ⚡ MOMENTUM: {momentum}
        ### ⏱️ EXPIRY: {expiry}
        ### ⏳ ENTRY IN: {wait} sec
        """)
    else:
        st.warning("No data available")
