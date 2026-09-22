import math
import re
import numpy as np
import pandas as pd
import config

# ============================================================
# TECHNICAL ANALYSIS & INDICATORS
# ============================================================

def EMA(series, period):
    return series.ewm(span=period, adjust=False).mean()

def RSI(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def ATR(df, period=14):
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def analyze_timeframe(df):
    if df is None or len(df) < 60:
        return {"score": 0.0, "trend": "UNKNOWN", "atr": np.nan, "rsi": np.nan}

    close = df["close"]
    ema20, ema50, ema100 = EMA(close, 20), EMA(close, 50), EMA(close, 100)
    rsi_val = RSI(close).iloc[-1]
    atr_val = ATR(df).iloc[-1]

    score = 0.0
    score += 0.25 if close.iloc[-1] > ema20.iloc[-1] else -0.25
    score += 0.30 if ema20.iloc[-1] > ema50.iloc[-1] else -0.30
    score += 0.20 if ema50.iloc[-1] > ema100.iloc[-1] else -0.20

    if 55 <= rsi_val <= 70: score += 0.15
    elif 70 < rsi_val <= 78: score += 0.05
    elif rsi_val > 78: score -= 0.08
    elif 30 <= rsi_val < 45: score -= 0.15
    elif rsi_val < 30: score += 0.05

    trend = "BULLISH" if score >= 0.18 else ("BEARISH" if score <= -0.18 else "NEUTRAL")
    return {"score": score, "trend": trend, "atr": atr_val, "rsi": rsi_val}

def price_action(df):
    if df is None or len(df) < 5: return 0.0, "UNKNOWN"
    curr, prev = df.iloc[-1], df.iloc[-2]
    c_range = max(curr["high"] - curr["low"], 1e-12)
    body = (curr["close"] - curr["open"]) / c_range
    score = np.clip(body * 0.9, -1, 1)
    if curr["close"] > prev["close"]: score += 0.15
    elif curr["close"] < prev["close"]: score -= 0.15
    score = np.clip(score, -1, 1)

    label = "STRONG_BULLISH" if score > 0.55 else ("BULLISH" if score > 0.15 else ("STRONG_BEARISH" if score < -0.55 else ("BEARISH" if score < -0.15 else "NEUTRAL")))
    return score, label

def breakout(df):
    if df is None or len(df) < 30: return 0.0, "NO_BREAKOUT"
    p_high = df["high"].iloc[-21:-1].max()
    p_low = df["low"].iloc[-21:-1].min()
    close = df["close"].iloc[-1]
    if close > p_high * 1.002: return 1.0, "BULLISH_BREAKOUT"
    if close < p_low * 0.998: return -1.0, "BEARISH_BREAKOUT"
    return 0.0, "NO_BREAKOUT"

def coin_news_sentiment(coin_name, symbol, news):
    base = symbol.split("/")[0].upper()
    matched = []
    IGNORED_SYMBOLS = {"NEAR", "FLOW", "GAIN", "RENT", "ONE", "UNI", "RAY", "KEY", "RUN"}

    for item in news:
        text = f"{item['title']} {item['summary']}".lower()
        name_match = (len(coin_name) >= 4 and coin_name.lower() in text)
        symbol_match = (base not in IGNORED_SYMBOLS and re.search(r"\b" + re.escape(base) + r"\b", text, re.I))

        if name_match or symbol_match:
            matched.append(item)

    if not matched:
        return {"news_score": 0.0, "news_sentiment": "NO_NEWS", "news_count": 0}

    return {"news_score": 0.2, "news_sentiment": "BULLISH", "news_count": len(matched)}
  
