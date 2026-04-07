import streamlit as st
import pandas as pd
import yfinance as yf
import time
from datetime import datetime

st.set_page_config(page_title="LEVEL 3 INSTITUTIONAL BOT", layout="wide")

# ===== STYLE =====
st.markdown("""
<style>
body {background:#0f172a; color:white; font-family:Arial;}
.header {text-align:center; font-size:30px; color:#22c55e;}
.box {
    background:#020617;
    padding:15px;
    border-radius:12px;
    margin:10px 0;
    box-shadow:0 0 12px rgba(0,255,200,0.2);
}
.buy {color:#22c55e; font-weight:bold;}
.sell {color:#ef4444; font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ===== SESSION =====
if "history" not in st.session_state:
    st.session_state.history = []

# ===== ASSETS =====
ASSETS = {
"EURUSD":"EURUSD=X",
"GBPUSD":"GBPUSD=X",
"USDJPY":"JPY=X",
"AUDUSD":"AUDUSD=X",
"EURJPY":"EURJPY=X",
"GBPJPY":"GBPJPY=X",
"XAUUSD":"GC=F"
}

# ===== DATA =====
def get_data(sym):
    try:
        df = yf.download(sym, interval="1m", period="1d", progress=False)

        if df is None or df.empty or len(df) < 100:
            return None

        df = df[['Open','High','Low','Close']].copy()
        df = df.apply(pd.to_numeric, errors='coerce').dropna()
        df = df[~df.index.duplicated(keep='last')]
        df.reset_index(drop=True, inplace=True)

        return df.tail(100)

    except:
        return None

# ===== INDICATORS =====
def indicators(df):
    df["EMA5"] = df["Close"].ewm(span=5).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["VOL"] = df["Close"].rolling(10).std().fillna(0)
    return df

# ===== ORDER BLOCK =====
def order_block(df):
    try:
        last = df.iloc[-5:]

        high = float(last["High"].max())
        low = float(last["Low"].min())
        close = float(df["Close"].iloc[-1].item())

        if close > high:
            return "BUY", "Breakout OB"
        elif close < low:
            return "SELL", "Breakdown OB"

        return None, None
    except:
        return None, None

# ===== LIQUIDITY =====
def liquidity(df):
    try:
        highs = df["High"]
        lows = df["Low"]

        last_high = float(highs.iloc[-2].item())
        prev_high = float(highs.iloc[-6:-2].max())

        last_low = float(lows.iloc[-2].item())
        prev_low = float(lows.iloc[-6:-2].min())

        close = float(df["Close"].iloc[-1].item())

        if last_high > prev_high and close < last_high:
            return "SELL", "Liquidity Grab High"
        elif last_low < prev_low and close > last_low:
            return "BUY", "Liquidity Grab Low"

        return None, None
    except:
        return None, None

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

        ob_dir, ob_reason = order_block(df)
        liq_dir, liq_reason = liquidity(df)

        if vol < 0.0003:
            return None

        score = 0
        reasons = []

        # PRIORITY: liquidity
        if liq_dir:
            direction = liq_dir
            score += 3
            reasons.append(liq_reason)

        # THEN order block
        elif ob_dir:
            direction = ob_dir
            score += 2
            reasons.append(ob_reason)

        else:
            if ema5 > ema20:
                direction = "BUY"
                reasons.append("Trend Up")
            else:
                direction = "SELL"
                reasons.append("Trend Down")
            score += 1

        confidence = min(97, 85 + score * 3)

        return direction, confidence, reasons

    except:
        return None

# ===== SIGNAL =====
def get_signal():
    best = None
    best_score = 0

    for name, sym in ASSETS.items():
        result = analyze(sym)

        if result is None:
            continue

        direction, confidence, reasons = result

        if confidence > best_score and confidence >= 88:
            best = (name, direction, confidence, reasons)
            best_score = confidence

    return best

# ===== UI =====
st.markdown('<div class="header">🏦 LEVEL 3 INSTITUTIONAL BOT</div>', unsafe_allow_html=True)

col1, col2 = st.columns([2,1])

# ===== AUTO BOT =====
with col1:
    auto = st.toggle("⚡ AUTO INSTITUTIONAL MODE", True)

    if auto:
        st.info("Scanning institutional setups...")

        signal = get_signal()

        if signal:
            pair, direction, confidence, reasons = signal
            now = datetime.now().strftime("%H:%M:%S")

            entry = {
                "pair": pair,
                "direction": direction,
                "confidence": confidence,
                "time": now,
                "reason": ", ".join(reasons),
                "retry": "WAIT"
            }

            st.session_state.history.insert(0, entry)

            color = "buy" if direction == "BUY" else "sell"

            st.markdown(f"""
            <div class="box">
            <b>{pair}</b><br>
            <span class="{color}">{direction}</span><br>
            🔥 {confidence}%<br>
            🕐 Trade: 2 MIN<br>
            🔁 Retry: If loss, re-enter once<br>
            ⏱ {now}<br>
            📊 {entry['reason']}
            </div>
            """, unsafe_allow_html=True)

        else:
            st.warning("No institutional setup... waiting")

        time.sleep(5)
        st.rerun()

# ===== HISTORY =====
with col2:
    st.subheader("📜 Live Feed")

    if len(st.session_state.history) == 0:
        st.write("No signals yet...")

    for h in st.session_state.history[:10]:
        color = "buy" if h["direction"] == "BUY" else "sell"

        st.markdown(f"""
        <div class="box">
        {h['pair']} - <span class="{color}">{h['direction']}</span><br>
        🔥 {h['confidence']}%<br>
        ⏱ {h['time']}
        </div>
        """, unsafe_allow_html=True)
