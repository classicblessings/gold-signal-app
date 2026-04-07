import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Trade AI", layout="centered")

st.title("🔥 Trade AI Signal (PRO)")

# --------- FAKE MARKET DATA (Replace later with real API) ----------
def generate_data():
    price = np.cumsum(np.random.randn(100)) + 100
    df = pd.DataFrame(price, columns=["close"])
    return df

df = generate_data()

# --------- INDICATORS ----------
def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df["RSI"] = calculate_rsi(df["close"])

df["EMA"] = df["close"].ewm(span=20).mean()

# --------- SIGNAL LOGIC ----------
def get_signal():
    rsi = df["RSI"].iloc[-1]
    price = df["close"].iloc[-1]
    ema = df["EMA"].iloc[-1]

    if rsi < 30 and price > ema:
        return "BUY", 80
    elif rsi > 70 and price < ema:
        return "SELL", 78
    else:
        return "WAIT", 60

signal, confidence = get_signal()

# --------- UI ----------
st.subheader("📊 Pair: EUR/USD OTC")

st.metric("Signal", signal)
st.metric("Confidence", f"{confidence}%")

# --------- ENTRY TIMER ----------
import time

st.subheader("⏱ Entry Timer")

timer = st.empty()

for i in range(5, 0, -1):
    timer.write(f"Enter in: {i} sec")
    time.sleep(1)

st.success("🚀 Enter Trade Now!")

# --------- BUTTONS ----------
col1, col2 = st.columns(2)

with col1:
    st.button("🟢 BUY")

with col2:
    st.button("🔴 SELL")

# --------- FOOTER ----------
st.info("Smart AI Trading Assistant (No fake promises)")
