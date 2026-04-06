import streamlit as st
import pandas as pd
import yfinance as yf
import random
import time
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="FINAL BOSS AI", layout="centered")

# ===== STYLE =====
st.markdown("""
<style>
body { background-color: #0d1117; }
h1 { color: #00ffcc; text-align:center; }
.stButton>button {
    background: linear-gradient(90deg,#00ffcc,#0077ff);
    color:black; border-radius:10px; height:3em; width:100%;
}
</style>
""", unsafe_allow_html=True)

# ===== PAIRS =====
PAIRS = {
    "EUR/USD OTC":"EURUSD=X",
    "GBP/USD OTC":"GBPUSD=X",
    "USD/JPY OTC":"JPY=X",
    "AUD/USD OTC":"AUDUSD=X",
    "USD/CAD OTC":"CAD=X",
    "EUR/JPY OTC":"EURJPY=X",
    "GBP/JPY OTC":"GBPJPY=X"
}

# ===== TIME =====
def now():
    return datetime.utcnow() + timedelta(hours=1)

def session():
    h = now().hour
    if 7<=h<13: return "LONDON 🔥"
    elif 13<=h<18: return "NEW YORK ⚡"
    return "LOW MARKET 💤"

def entry_time():
    s = now().second
    return s if s<=10 else 60-s

# ===== NOTIFY =====
def notify():
    st.markdown("""
    <script>
    var a=new Audio("https://www.soundjay.com/buttons/sounds/button-3.mp3");
    a.play(); alert("🚨 SNIPER SIGNAL!");
    </script>
    """, unsafe_allow_html=True)

# ===== DATA =====
def get_data(sym):
    try:
        df = yf.download(sym, interval="1m", period="1d", progress=False)
        if df is None or df.empty or len(df)<30:
            return None
        df = df[['Open','High','Low','Close']].dropna().copy()
        for c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
        df = df.dropna().reset_index(drop=True)
        return df.tail(50)
    except:
        return None

# ===== INDICATORS =====
def rsi(df):
    d = df["Close"].diff()
    g = d.clip(lower=0).rolling(14).mean()
    l = -d.clip(upper=0).rolling(14).mean()
    rs = g/l
    return (100-(100/(1+rs))).fillna(50)

def pattern(df):
    if len(df)<2: return "NONE"
    a,b = df.iloc[-1], df.iloc[-2]
    if b["Close"]<b["Open"] and a["Close"]>a["Open"]: return "BULLISH 📈"
    if b["Close"]>b["Open"] and a["Close"]<a["Open"]: return "BEARISH 📉"
    return "NONE"

def confirm(df, d):
    last = df.iloc[-1]
    if d=="CALL 📈": return float(last["Close"])>float(last["Open"])
    if d=="PUT 📉": return float(last["Close"])<float(last["Open"])
    return False

# ===== ANALYZE =====
def analyze(sym):
    df = get_data(sym)
    if df is None: return None
    try:
        df["EMA"] = df["Close"].ewm(span=20).mean()
        df["RSI"] = rsi(df)

        c = float(df["Close"].iloc[-1])
        e = float(df["EMA"].iloc[-1])
        r = float(df["RSI"].iloc[-1])

        trend = "UPTREND" if c>e else "DOWNTREND"
        pat = pattern(df)

        return df,trend,pat,r
    except:
        return None

# ===== SIGNAL =====
def best_signal():
    best=None; score_max=0

    for name,sym in PAIRS.items():
        r = analyze(sym)
        if not r: continue

        df,trend,pat,rsi_val = r

        call=0; put=0

        if trend=="UPTREND": call+=2
        else: put+=2

        if rsi_val<45: call+=1
        elif rsi_val>55: put+=1

        if "BULLISH" in pat: call+=2
        elif "BEARISH" in pat: put+=2

        direction = "CALL 📈" if call>put else "PUT 📉" if put>call else None
        if not direction: continue

        if not confirm(df,direction): continue

        s = max(call,put)
        w = entry_time()

        if w>50: continue

        if s>score_max:
            best={
                "pair":name,
                "dir":direction,
                "wait":w,
                "conf":min(99,80+s*3)
            }
            score_max=s

    return best

# ===== HISTORY =====
if "hist" not in st.session_state:
    st.session_state.hist=[]

# ===== UI =====
st.markdown("<h1>💀 FINAL BOSS AI</h1>",unsafe_allow_html=True)
st.write("🕒",now().strftime("%H:%M:%S"),"(WAT)")
st.write("📊",session())

auto = st.toggle("🔄 AUTO SCAN",False)

# ===== AUTO =====
if auto:
    box = st.empty()
    while True:
        s = best_signal()
        with box.container():
            if s:
                notify()
                st.success("🚨 SIGNAL")
                st.write(s)
                st.session_state.hist.insert(0,s)
                st.session_state.hist = st.session_state.hist[:10]
            else:
                st.warning("No setup")
        time.sleep(5)
        st.rerun()

# ===== MANUAL =====
if st.button("🎯 GET SIGNAL"):
    s = best_signal()
    if s:
        notify()
        st.success("🚨 SIGNAL")
        st.write(s)
        st.session_state.hist.insert(0,s)
        st.session_state.hist = st.session_state.hist[:10]
    else:
        st.warning("No setup")

# ===== HISTORY =====
st.markdown("### 📜 HISTORY")
for h in st.session_state.hist:
    st.write(h)
