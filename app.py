import streamlit as st
import pandas as pd
import yfinance as yf
import datetime

st.set_page_config(layout="wide")

# ===== AUTO REFRESH =====
st.markdown('<meta http-equiv="refresh" content="6">', unsafe_allow_html=True)

# ===== STYLE =====
st.markdown("""
<style>
.signal {
    text-align:center;
    font-size:55px;
    font-weight:bold;
    padding:25px;
    border-radius:20px;
}
.buy {background:#00e676;color:#000;}
.sell {background:#ff1744;color:#fff;}
.wait {background:#1f2937;color:#aaa;}
.card {
    background:#111827;
    padding:15px;
    border-radius:15px;
    margin-top:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("⚡ IQ OPTION FINAL BOSS AI")

# ===== SETTINGS =====
min_conf = st.slider("Min Confidence %", 85, 97, 92)

# ===== TIME =====
now = datetime.datetime.utcnow()
sec = now.second

# ===== PAIRS =====
pairs = ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","USDCAD=X"]

# ===== DATA =====
@st.cache_data(ttl=5)
def get_data(symbol):
    try:
        df = yf.download(symbol, period="1d", interval="1m")
        if df.empty:
            return None
        return df
    except:
        return None

# ===== INDICATORS =====
def compute(df):
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA20'] = df['Close'].rolling(20).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Momentum'] = df['Close'].diff(3)
    df['Volatility'] = df['Close'].rolling(10).std()

    return df.dropna()

# ===== SIGNAL ENGINE =====
def get_signal(df):
    last = df.iloc[-1]
    score = 0

    # TREND
    if last['MA5'] > last['MA20']:
        score += 2
    else:
        score -= 2

    # MOMENTUM
    score += 1 if last['Momentum'] > 0 else -1

    # RSI EXTREME
    if last['RSI'] < 25:
        score += 2
    elif last['RSI'] > 75:
        score -= 2

    # VOLATILITY FILTER
    if last['Volatility'] < df['Volatility'].mean():
        return "WAIT", 0

    confidence = min(97, max(70, 60 + score * 8))

    if score >= 4:
        return "BUY", confidence
    elif score <= -4:
        return "SELL", confidence
    return "WAIT", confidence

# ===== BACKTEST =====
def backtest(df):
    wins = 0
    losses = 0

    for i in range(30, len(df)-2):
        sub = df.iloc[:i]
        signal, _ = get_signal(sub)

        if signal == "WAIT":
            continue

        entry = df.iloc[i]['Close']
        result = df.iloc[i+1]['Close']

        if signal == "BUY" and result > entry:
            wins += 1
        elif signal == "SELL" and result < entry:
            wins += 1
        else:
            losses += 1

    total = wins + losses
    winrate = (wins / total * 100) if total > 0 else 0
    return winrate

# ===== SCAN =====
best = None

for pair in pairs:
    df = get_data(pair)
    if df is None:
        continue

    df = compute(df)

    if len(df) < 50:
        continue

    signal, conf = get_signal(df)

    if signal == "WAIT" or conf < min_conf:
        continue

    wr = backtest(df)

    # combine real + backtest confidence
    final_conf = (conf * 0.6) + (wr * 0.4)

    if best is None or final_conf > best["score"]:
        # trade timing logic
        last = df.iloc[-1]
        strong_move = abs(last['Momentum']) > df['Momentum'].std()

        if strong_move:
            ttime = "30s - 60s ⚡"
        else:
            ttime = "1 - 3 min 🧠"

        best = {
            "pair": pair,
            "signal": signal,
            "conf": final_conf,
            "time": ttime,
            "wr": wr
        }

# ===== DISPLAY =====
if best is None:
    display = "WAIT"
    cls = "wait"
    pair = "-"
    conf = 0
    ttime = "-"
    wr = 0
else:
    display = f"{best['signal']}\n{best['pair']}"
    cls = "buy" if best['signal']=="BUY" else "sell"
    pair = best['pair']
    conf = best['conf']
    ttime = best['time']
    wr = best['wr']

# SNIPER ENTRY FILTER
if sec < 50:
    display = "PREPARE"
    cls = "wait"
elif sec < 58:
    display = "GET READY"
    cls = "wait"

st.markdown(f"<div class='signal {cls}'>{display}<br>{conf:.0f}%</div>", unsafe_allow_html=True)

# ===== INFO =====
st.markdown("<div class='card'>", unsafe_allow_html=True)
st.write(f"🎯 Pair: {pair}")
st.write(f"⏱ Trade Time: {ttime}")
st.write(f"📊 Backtest Winrate: {wr:.1f}%")
st.write(f"🧠 Final Confidence: {conf:.1f}%")
st.write(f"⏰ UTC: {now.strftime('%H:%M:%S')}")
st.markdown("</div>", unsafe_allow_html=True)

# ===== CHART =====
if best is not None:
    df = get_data(pair)
    if df is not None:
        st.line_chart(df['Close'].tail(100))
