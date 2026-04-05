from datetime import datetime, timezone, timedelta
import pandas as pd
import json
import os

# ================================
# ⚙️ SETTINGS
# ================================

MIN_CONFIDENCE = 95
WAT_OFFSET = timedelta(hours=1)
STATS_FILE = "pair_stats.json"

ALL_PAIRS = [
    "EURUSD","GBPUSD","USDJPY","USDCHF",
    "AUDUSD","USDCAD","NZDUSD",
    "EURJPY","GBPJPY","AUDJPY","CADJPY",
    "EURGBP","EURAUD","EURCAD",
    "GBPCHF","GBPAUD","GBPCAD",
    "XAUUSD"
]

# ================================
# ⏰ TIME + SESSION
# ================================

def get_wat_time():
    return datetime.now(timezone.utc) + WAT_OFFSET

def get_session():
    hour = get_wat_time().hour

    if 8 <= hour < 11:
        return "LONDON"
    elif 14 <= hour < 17:
        return "NEW_YORK"
    elif 18 <= hour < 21:
        return "EVENING"
    return None

# ================================
# 📰 NEWS FILTER (BASIC)
# ================================

def is_news_time():
    # Avoid top of the hour (common news spikes)
    minute = get_wat_time().minute
    return minute < 5 or minute > 55

# ================================
# 📊 INDICATORS
# ================================

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ================================
# 🕯️ CANDLE CONFIRMATION
# ================================

def is_bullish_engulfing(df):
    c1, c2 = df.iloc[-2], df.iloc[-1]
    return c1["close"] < c1["open"] and c2["close"] > c2["open"] and c2["close"] > c1["open"]

def is_bearish_engulfing(df):
    c1, c2 = df.iloc[-2], df.iloc[-1]
    return c1["close"] > c1["open"] and c2["close"] < c2["open"] and c2["close"] < c1["open"]

def rejection_wick(df):
    last = df.iloc[-1]
    body = abs(last["close"] - last["open"])
    wick = last["high"] - last["low"]
    return wick > body * 2  # strong rejection

# ================================
# ⏱️ EXPIRY LOGIC
# ================================

def get_expiry(df):
    last_candle_size = abs(df.iloc[-1]["close"] - df.iloc[-1]["open"])

    if last_candle_size > df["close"].std():
        return "1m"  # strong move → quick entry
    return "5m"      # slower trend

# ================================
# 📊 WIN RATE TRACKER
# ================================

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def get_win_rate(pair, stats):
    if pair not in stats:
        return 0.5
    wins = stats[pair].get("wins", 0)
    losses = stats[pair].get("losses", 0)
    total = wins + losses
    return wins / total if total > 0 else 0.5

# ================================
# 🧠 ANALYSIS ENGINE
# ================================

def analyze(pair, stats):

    df = get_candles(pair)  # 🔥 CONNECT YOUR DATA HERE

    if df is None or len(df) < 50:
        return None

    df["EMA20"] = df["close"].ewm(span=20).mean()
    df["EMA50"] = df["close"].ewm(span=50).mean()
    df["RSI"] = rsi(df["close"])

    last = df.iloc[-1]

    trend_up = last["EMA20"] > last["EMA50"]
    trend_down = last["EMA20"] < last["EMA50"]

    win_rate = get_win_rate(pair, stats)

    confidence = 0

    # ================= BUY =================
    if trend_up and df["RSI"].iloc[-1] > 50:
        if is_bullish_engulfing(df) or rejection_wick(df):
            confidence = 95 + (win_rate * 5)

            return {
                "pair": pair,
                "direction": "BUY",
                "confidence": round(confidence, 2),
                "expiry": get_expiry(df)
            }

    # ================= SELL =================
    if trend_down and df["RSI"].iloc[-1] < 50:
        if is_bearish_engulfing(df) or rejection_wick(df):
            confidence = 95 + (win_rate * 5)

            return {
                "pair": pair,
                "direction": "SELL",
                "confidence": round(confidence, 2),
                "expiry": get_expiry(df)
            }

    return None

# ================================
# 🏆 FINAL BOSS ENGINE
# ================================

def run_final_boss():

    session = get_session()

    if not session:
        print("⛔ No session")
        return

    if is_news_time():
        print("⚠️ Avoiding news spike time")
        return

    print(f"\n⚡ FINAL BOSS — {session} SESSION\n")

    stats = load_stats()
    best_signal = None

    for pair in ALL_PAIRS:

        signal = analyze(pair, stats)

        if not signal:
            continue

        if signal["confidence"] >= MIN_CONFIDENCE:

            if best_signal is None or signal["confidence"] > best_signal["confidence"]:
                best_signal = signal

    print("\n====================")

    if best_signal:
        print("🏆 ELITE SIGNAL:")
        print(best_signal)
    else:
        print("❌ No clean setup (GOOD DISCIPLINE)")

# ================================
# ▶️ RUN
# ================================

if __name__ == "__main__":
    run_final_boss()
