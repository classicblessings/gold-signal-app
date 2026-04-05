import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(layout="wide")

# ===== AUTO REFRESH =====
st.markdown('<meta http-equiv="refresh" content="6">', unsafe_allow_html=True)

# ===== UI STYLE =====
st.markdown("""
<style>
body {background-color:#0b0f1a;}

.signal {
    text-align:center;
    font-size:65px;
    font-weight:bold;
    padding:25px;
    border-radius:20px;
}

.buy {background:#00e676;color:#000;}
.sell {background:#ff1744;color:#fff;}
.wait {background:#1f2937;color:#aaa;}

.timer {text-align:center;font-size:24px;color:#ccc;}

.card {
    background:#111827;
    padding:15px;
    border-radius:15px;
    margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📡 GOLD OTC SMART AI SIGNAL")

# ===== MODE =====
mode = st.radio("Mode", ["Auto Session", "Manual Scan"])

# ===== SETTINGS =====
col1, col2 = st.columns(2)
min_conf = col1.slider("Min Confidence %", 85, 95, 90)
session = col2.selectbox("Session", ["Morning","Afternoon","Evening"])

# ===== SESSION =====
hour = datetime.datetime.now().hour
sessions = {
    "Morning": (6,12),
    "Afternoon": (12,18),
    "Evening": (18,23)
}
start, end = sessions[session]

# ===== DATA =====
@st.cache_data(ttl=5)
def get_data():
    try:
        return yf.download("XAUUSD=X", period="1d", interval="1m")
    except:
        return pd.DataFrame()

# ===== SMART AI ANALYSIS =====
def analyze(df):
    if df is None or df.empty or len(df) < 50:
        return "WAIT", 0

    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # Momentum
    df['Momentum'] = df['Close'].diff(5)

    # Volatility
    df['Volatility'] = df['Close'].rolling(10).std()

    df = df.dropna()
    if df.empty:
        return "WAIT", 0

    last = df.iloc[-1]

    score = 0

    # Trend
    score += 2 if last['MA5'] > last['MA20'] else -2

    # Momentum
    score += 1 if last['Momentum'] > 0 else -1

    # RSI
    if last['RSI'] < 30:
        score += 2
    elif last['RSI'] > 70:
        score -= 2

    # Volatility filter
    if last['Volatility'] < df['Volatility'].mean():
        return "WAIT", 0

    confidence = min(95, max(60, 65 + (score * 7)))

    if score >= 3:
        return "BUY", confidence
    elif score <= -3:
        return "SELL", confidence
    else:
        return "WAIT", confidence

# ===== MAIN =====
df = get_data()
signal, conf = analyze(df)

now = datetime.datetime.now()
sec = now.second

# ===== LOGIC =====
if mode == "Manual Scan":
    timer = 30 - (sec % 30)

    if conf < min_conf:
        display = "WAIT"
        cls = "wait"
    else:
        display = signal
        cls = "buy" if signal == "BUY" else "sell"

    st.markdown(f"<div class='signal {cls}'>{display}<br>{conf:.0f}%</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='timer'>⚡ Refresh in: {timer}s</div>", unsafe_allow_html=True)

else:
    timer = 60 - sec

    if not (start <= hour < end):
        display = "SESSION CLOSED"
        cls = "wait"

    elif conf < min_conf:
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

    st.markdown(f"<div class='signal {cls}'>{display}<br>{conf:.0f}%</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='timer'>⏱ Entry in: {timer}s</div>", unsafe_allow_html=True)

# ===== INFO PANEL =====
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.write(f"🧠 Confidence: {conf:.0f}%")
st.write(f"⏰ Time: {now.strftime('%H:%M:%S')}")
st.write(f"📊 Mode: {mode}")
st.markdown("</div>", unsafe_allow_html=True)

# ===== CHART =====
if not df.empty:
    st.line_chart(df['Close'].tail(100))
else:
    st.warning("Waiting for market data...")
