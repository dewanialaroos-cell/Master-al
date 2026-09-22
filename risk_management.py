import math
import numpy as np
import config

def calculate_trade_levels(price, signal, df_ohlcv, atr_value, tech_score=50):
    """
    Liquidation Resistant SL with Dynamic AI-Driven Take Profit (Flexible R:R)
    """
    if not math.isfinite(price) or price <= 0:
        return np.nan, np.nan

    # 1. ATR Safeguard
    if not math.isfinite(atr_value) or atr_value <= 0:
        atr_value = price * 0.02
    else:
        atr_value = min(atr_value, price * config.DEFAULT_ATR_CAP_PERCENT)

    # 2. Swing High / Swing Low Structure Detection
    if df_ohlcv is not None and len(df_ohlcv) >= 20:
        recent_low = df_ohlcv["low"].iloc[-20:].min()
        recent_high = df_ohlcv["high"].iloc[-20:].max()
    else:
        recent_low = price - (1.5 * atr_value)
        recent_high = price + (1.5 * atr_value)

    # 3. Dynamic Buffer for Stop Loss (Anti-Wick Hunting)
    score_factor = max(0.8, (100 - tech_score) / 50.0)
    liquidation_buffer = (config.SL_ATR_MULTIPLIER * atr_value) * score_factor

    # 4. Dynamic Reward Multiplier (AI Momentum Based R:R)
    # Agar Tech Score bohot strong hai (e.g. 80+), toh AI R:R ko 1:4 ya 1:5 tak badha dega
    if tech_score >= 80:
        reward_multiplier = 4.5  # Super Strong Trend (High Reward Target)
    elif tech_score >= 72:
        reward_multiplier = 3.2  # Strong Trend
    elif tech_score >= 63:
        reward_multiplier = 2.2  # Moderate Trend
    else:
        reward_multiplier = 1.8  # Standard Min Target

    if signal == "LONG":
        # SL calculation below recent swing low
        structure_sl = recent_low - (0.5 * atr_value)
        atr_sl = price - liquidation_buffer
        stop_loss = min(structure_sl, atr_sl)
        
        # Risk & Dynamic Take Profit Target
        risk = price - stop_loss
        take_profit = price + (risk * reward_multiplier)

    elif signal == "SHORT":
        # SL calculation above recent swing high
        structure_sl = recent_high + (0.5 * atr_value)
        atr_sl = price + liquidation_buffer
        stop_loss = max(structure_sl, atr_sl)
        
        # Risk & Dynamic Take Profit Target
        risk = stop_loss - price
        take_profit = max(price - (risk * reward_multiplier), price * 0.70)
        
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
    
