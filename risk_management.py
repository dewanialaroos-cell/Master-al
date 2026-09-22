import math
import numpy as np
import config

def calculate_trade_levels(price, signal, atr_value):
    if not math.isfinite(price) or price <= 0:
        return np.nan, np.nan

    # Dynamic ATR Volatility Cap
    if not math.isfinite(atr_value) or atr_value <= 0:
        atr_value = price * 0.02
    else:
        atr_value = min(atr_value, price * config.DEFAULT_ATR_CAP_PERCENT)

    if signal == "LONG":
        stop_loss = price - (config.SL_ATR_MULTIPLIER * atr_value)
        take_profit = price + (config.TP_ATR_MULTIPLIER * atr_value)
    elif signal == "SHORT":
        stop_loss = price + (config.SL_ATR_MULTIPLIER * atr_value)
        take_profit = max(price - (config.TP_ATR_MULTIPLIER * atr_value), price * 0.85)
    else:
        stop_loss, take_profit = np.nan, np.nan

    return round(stop_loss, 6), round(take_profit, 6)

def generate_signal(technical_score):
    raw_score = ((technical_score - 50) / 50) * 32
    long_score = np.clip(50 + raw_score, 0, 95)
    short_score = np.clip(50 - raw_score, 0, 95)

    signal = "NO TRADE"
    if long_score >= 63 and long_score > short_score + 5:
        signal = "LONG"
    elif short_score >= 63 and short_score > long_score + 5:
        signal = "SHORT"

    return signal, round(long_score, 2), round(short_score, 2)
