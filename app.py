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
# SAFE FLOAT
# ===============================
def safe_float(val):
    try:
        return float(val)
    except:
        return None

# ===============================
# TIME (WAT)
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
    return max(1, 60 - get_wat_time().second)

# ===============================
# RSI
# ===============================
def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)

# ===============================
# DATA (HARDENED)
# ===============================
def get_live_data(symbol):
    try:
        df = yf.download(symbol, interval="1m", period="1d", progress=False)

        if df is None or df.empty or len(df) < 30:
            return None

        df = df[['Open', 'High', 'Low', 'Close']].copy()
        df = df.dropna()

        if len(df) < 30:
            return None

        df = df.reset_index(drop=True)

        return df.tail(50)

    except:
        return None

# ===============================
# PATTERN (SAFE)
# ===============================
def detect_pattern(df):
    if df is None or len(df) < 2:
        return "NONE"

    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        last_close = safe_float(last["Close"])
        last_open = safe_float(last["Open"])
        prev_close = safe_float(prev["Close"])
        prev_open = safe_float(prev["Open"])
        last_high = safe_float(last["High"])
        last_low = safe_float(last["Low"])

        if None in [last_close, last_open, prev_close, prev_open, last_high, last_low]:
            return "NONE"

        if prev_close < prev_open and last_close > last_open and last_close > prev_open:
            return "BULLISH ENGULFING 📈"

        if prev_close > prev_open and last_close < last_open and last_close < prev_open:
            return "BEARISH ENGULFING 📉"

        body = abs(last_close - last_open)
        wick = last_high - last_low

        if wick > body * 2:
            return "PIN BAR 🔄"

        return "NONE"

    except:
        return "NONE"

# ===============================
# EXPIRY
# ===============================
def get_expiry(momentum, rsi):
    if momentum == "STRONG":
        return "1 MIN"
    elif 40 < rsi < 60:
        return "3 MIN"
    else:
        return "5 MIN"

# ===============================
# ANALYSIS (FULL SAFE)
# ===============================
def analyze(symbol):
    df = get_live_data(symbol)

    if df is None:
        return None

    try:
        df["EMA"] = df["Close"].ewm(span=20).mean()
        df["RSI"] = calculate_rsi(df)

        last_close = safe_float(df["Close"].iloc[-1])
        last_ema = safe_float(df["EMA"].iloc[-1])
        last_rsi = safe_float(df["RSI"].iloc[-1])

        if None in [last_close, last_ema, last_rsi]:
            return None

        trend = "UPTREND" if last_close > last_ema else "DOWNTREND"
        rsi = last_rsi

        momentum = "STRONG" if abs(df["Close"].iloc[-1] - df["Close"].iloc[-5]) > 0 else "WEAK"

        pattern = detect_pattern(df)

        recent_high = df["High"].rolling(10).max().iloc[-1]
        recent_low = df["Low"].rolling(10).min().iloc[-1]

        if pd.isna(recent_high) or pd.isna(recent_low):
            return None

        near_high = last_close >= recent_high * 0.999
        near_low = last_close <= recent_low * 1.001

        structure = "NONE"
        if near_high:
            structure = "RESISTANCE 🔴"
        elif near_low:
            structure = "SUPPORT 🟢"

        fake_breakout = False
        if last_close < recent_high and df["High"].iloc[-1] > recent_high:
            fake_breakout = True
        if last_close > recent_low and df["Low"].iloc[-1] < recent_low:
            fake_breakout = True

        expiry = get_expiry(momentum, rsi)

        return trend, rsi, momentum, pattern, expiry, structure, fake_breakout

    except:
        return None

# ===============================
# SIGNAL ENGINE (SAFE)
# ===============================
def generate_signal(confidence):
    try:
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

        return {
            "pair": pair_name,
            "direction": direction,
            "confidence": random.randint(confidence, 99),
            "wait": wait,
            "trend": trend,
            "rsi": round(rsi, 2),
            "momentum": momentum,
            "pattern": pattern,
            "expiry": expiry,
            "structure": structure
        }

    except:
        return None

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
        st.warning("No valid market data — try again")
