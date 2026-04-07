import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

st.set_page_config(page_title="AI MULTI ASSET BOT", layout="wide")

# ===== STYLE =====
st.markdown("""
<style>
body {background:#0f172a; color:white; font-family:Arial;}
.header {text-align:center; font-size:28px; color:#22c55e;}
.box {
    background:#020617;
    padding:15px;
    border-radius:10px;
    margin:10px 0;
}
.buy {color:#22c55e;}
.sell {color:#ef4444;}
</style>
""", unsafe_allow_html=True)

# ===== SESSION =====
if "history" not in st.session_state:
    st.session_state.history = []

# ===== ASSETS (MORE OPTIONS) =====
ASSETS = {
"EURUSD":"EURUSD=X",
"GBPUSD":"GBPUSD=X",
"USDJPY":"JPY=X",
"AUDUSD":"AUDUSD=X",
"EURJPY":"EURJPY=X",
"GBPJPY":"GBPJPY=X",
"XAUUSD":"GC=F",
"US30":"^DJI",
"NAS100":"^NDX"
}

# ===== DATA =====
def get_data(sym):
    try:
        df = yf.download(sym, interval="1m", period="1d", progress=False)
        if df is None or df.empty or len(df) < 80:
            return None

        df = df[['Open','High','Low','Close']].copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df = df[~df.index.duplicated(keep='last')]
        df.reset_index(drop=True, inplace=True)

        return df.tail(80)
    except:
        return None

# ===== INDICATORS =====
def indicators(df):
    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["VOL"] = df["Close"].rolling(10).std().fillna(0)
    return df

# ===== ANALYZE =====
def analyze(sym):
    df = get_data(sym)
    if df is None:
        return None

    try:
        df = indicators(df)

        ema5 = float(df["EMA5"].iloc[-1].item())
        ema20 = float(df["EMA20"].iloc[-1].item())
        vol = float(df["VOL"].iloc[-1].item())

        if vol < 0.0003:
            return None

        score = 0
        reasons = []

        if ema5 > ema20:
            direction = "BUY"
            score += 2
            reasons.append("Trend Up")
        else:
            direction = "SELL"
            score += 2
            reasons.append("Trend Down")

        confidence = min(92, 85 + score * 2)

        return direction, confidence, reasons

    except:
        return None

# ===== GET MULTIPLE SIGNALS =====
def get_signals():
    signals = []

    for name, sym in ASSETS.items():
        result = analyze(sym)

        if result is None:
            continue

        direction, confidence, reasons = result

        if confidence >= 88:
            signals.append((name, direction, confidence, reasons))

    # sort best first
    signals = sorted(signals, key=lambda x: x[2], reverse=True)

    return signals[:5]  # top 5

# ===== UI =====
st.markdown('<div class="header">🤖 MULTI-ASSET AI BOT</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2,1])

# ===== AUTO MODE =====
with col1:
    auto = st.toggle("⚡ AUTO MODE", True)

    if auto:
        st.info("Scanning all assets...")

        signals = get_signals()

        if signals:
            now = datetime.now().strftime("%H:%M:%S")

            for pair, direction, confidence, reasons in signals:

                entry = {
                    "pair": pair,
                    "direction": direction,
                    "confidence": confidence,
                    "time": now
                }

                st.session_state.history.insert(0, entry)

                color = "buy" if direction == "BUY" else "sell"

                st.markdown(f"""
                <div class="box">
                <b>{pair}</b><br>
                <span class="{color}">{direction}</span><br>
                🔥 {confidence}%<br>
                🕐 2 MIN TRADE<br>
                ⏱ {now}
                </div>
                """, unsafe_allow_html=True)

        else:
            st.warning("No strong setups — WAIT")

        time.sleep(6)
        st.rerun()

# ===== HISTORY =====
with col2:
    st.subheader("📜 History")

    for h in st.session_state.history[:10]:
        color = "buy" if h["direction"] == "BUY" else "sell"

        st.markdown(f"""
        <div class="box">
        {h['pair']} - <span class="{color}">{h['direction']}</span><br>
        🔥 {h['confidence']}%<br>
        ⏱ {h['time']}
        </div>
        """, unsafe_allow_html=True)
