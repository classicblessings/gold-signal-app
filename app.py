import streamlit as st
import pandas as pd
import yfinance as yf
import datetime, time

st.set_page_config(layout="wide")

st.title("🚀 GOLD SIGNAL PANEL (IQ OPTION STYLE)")

strength = st.slider("Signal Strength (%)", 60, 95, 80)

def get_data():
    return yf.download("XAUUSD=X", period="1d", interval="1m")

def analyze(df):
    df['MA5']=df['Close'].rolling(5).mean()
    df['MA12']=df['Close'].rolling(12).mean()
    df=df.dropna()
    last=df.iloc[-1]

    if last['MA5'] > last['MA12']:
        return "BUY", 80
    else:
        return "SELL", 80

placeholder = st.empty()

while True:
    df = get_data()
    signal, conf = analyze(df)

    now = datetime.datetime.now()
    sec = now.second

    if sec < 50:
        display = "PREPARE"
    elif sec < 58:
        display = "GET READY"
    else:
        display = signal

    placeholder.metric("Signal", display)
    st.write("Time:", now.strftime("%H:%M:%S"))
    st.line_chart(df['Close'])

    time.sleep(5)
