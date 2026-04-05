import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(layout="wide")

# ===== AUTO REFRESH =====
st.markdown(
    '<meta http-equiv="refresh" content="10">',
    unsafe_allow_html=True
)

# ===== STYLE =====
st.markdown("""
<style>
body {background-color:#0e0e0e;}

.signal-box {
    text-align:center;
    font-size:60px;
    font-weight:bold;
    padding:25px;
    border-radius:20px;
    margin-top:30px;
}

.buy {background:#00c853;color:white;}
.sell {background:#ff1744;color:white;}
.wait {background:#2c2c2c;color:#aaa;}

.timer {
    text-align:center;
    font-size:30px;
    color:#ccc;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 GOLD SIGNAL PANEL (IQ STYLE)")

strength = st.slider("Signal Strength (%)", 60, 95, 80)

# ===== DATA =====
@st.cache_data(ttl=10)
def get_data():
    try:
        df = yf.download("XAUUSD=X", period="1d", interval="1m")
        return df
    except:
        return pd.DataFrame()

# ===== ANALYSIS =====
def analyze(df):
    if df is None or df.empty or len(df) < 15:
        return "WAIT", 0

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA12'] = df['Close'].rolling(12).mean()
    df = df.dropna()

    if df.empty:
        return "WAIT", 0

    last = df.iloc[-1]

    if last['MA5'] > last['MA12']:
        return "BUY", 80
    else:
        return "SELL", 80

# ===== MAIN =====
df = get_data()
signal, conf = analyze(df)

now = datetime.datetime.now()
sec = now.second
countdown = 60 - sec

# ===== SIGNAL LOGIC =====
if signal == "WAIT":
    display = "WAIT"
    cls = "wait"

elif conf < strength:
    display = "WAIT"
    cls = "wait"

elif sec < 50:
    display = "PREPARE"
    cls = "wait"

elif sec < 58:
    display = "GET READY"
    cls = "wait"

else:
    display = signal
    cls = "buy" if signal == "BUY" else "sell"

# ===== UI =====
st.markdown(
    f"<div class='signal-box {cls}'>{display}<br>{conf}%</div>",
    unsafe_allow_html=True
)

st.markdown(
    f"<div class='timer'>⏱ Entry in: {countdown}s</div>",
    unsafe_allow_html=True
)

if not df.empty:
    st.line_chart(df['Close'])
else:
    st.warning("Waiting for market data...")
