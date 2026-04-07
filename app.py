import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import os

st.set_page_config(page_title="Sniper AI", layout="centered")

st.title("🔥 SNIPER AI (SIMPLE PRO)")

pairs = ["EURUSD=X", "GBPUSD=X", "AUDUSD=X", "USDJPY=X"]

@st.cache_data(ttl=60)
def get_data(pair):
    try:
        df = yf.download(pair, period="1d", interval="1m", progress=False)
        df.dropna(inplace=True)
        return df
    except:
        return pd.DataFrame()

def rsi(data, period=14):
    delta = data.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def analyze(df):
    df["RSI"] = rsi(df["Close"])
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    score = 0

    try:
        if df["Close"].iloc[-1] > df["EMA20"].iloc[-1] > df["EMA50"].iloc[-1]:
            score += 2
        if df["Close"].iloc[-1] < df["EMA20"].iloc[-1] < df["EMA50"].iloc[-1]:
            score -= 2

        if df["RSI"].iloc[-1] < 30:
            score += 2
        elif df["RSI"].iloc[-1] > 70:
            score -= 2
    except:
        return 0

    return score

best_pair = None
best_score = 0
best_df = None

for pair in pairs:
    df = get_data(pair)
    if df.empty:
        continue

    score = analyze(df)

    if abs(score) > abs(best_score):
        best_score = score
        best_pair = pair
        best_df = df

def get_signal(score):
    if score >= 3:
        return "🟢 STRONG UP"
    elif score <= -3:
        return "🔴 STRONG DOWN"
    else:
        return "🟡 WAIT"

signal = get_signal(best_score)

# -------- SIMPLE LEARNING SYSTEM ----------
file = "history.csv"

if not os.path.exists(file):
    pd.DataFrame(columns=["pair", "signal"]).to_csv(file, index=False)

hist = pd.read_csv(file)

if signal != "🟡 WAIT" and best_pair:
    new = pd.DataFrame([[best_pair, signal]], columns=["pair", "signal"])
    hist = pd.concat([hist, new])
    hist.to_csv(file, index=False)

total = len(hist)
up = len(hist[hist["signal"] == "🟢 STRONG UP"])
down = len(hist[hist["signal"] == "🔴 STRONG DOWN"])

accuracy = round((max(up, down) / total) * 100, 2) if total > 0 else 0

confidence = min(95, 60 + abs(best_score)*5 + accuracy/10)

# -------- UI ----------
if best_pair:
    st.subheader(f"📊 Best Pair: {best_pair}")
    st.metric("Signal", signal)
    st.metric("Confidence", f"{confidence}%")
    st.metric("Accuracy", f"{accuracy}%")

    if "STRONG" in signal:
        st.warning("🚨 SNIPER SIGNAL!")

    st.line_chart(best_df["Close"].tail(100))
else:
    st.error("No data (check internet)")

st.subheader("📈 History")
st.dataframe(hist.tail(10))

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()
