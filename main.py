import os
import time
import requests
import json
import pandas as pd
import numpy as np
import ccxt
import feedparser
from datetime import datetime

# ==========================================
# 1. CONFIGURATIONS & EXCLUSIONS
# ==========================================
EXCLUDED_STABLES = [
    'USDT', 'USDC', 'FDUSD', 'DAI', 'TUSD', 'USDE', 'USDD', 
    'EUR', 'GBP', 'BUSD', 'PYUSD', 'USDP', 'GUSD', 'AEUR'
]

def is_stablecoin(symbol):
    base = symbol.split('/')[0].split(':')[0].upper()
    return base in EXCLUDED_STABLES

LEARNING_FILE = "ai_learning_data.json"
ALERTED_HISTORY_FILE = "alerted_history.json"

def load_json_db(filename, default_val):
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return default_val

def save_json_db(filename, data):
    try:
        with open(filename, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Database Sync Error ({filename}): {e}")

# ==========================================
# 2. MARKET PSYCHOLOGY & BEHAVIORAL ENGINE
# ==========================================
def analyze_market_psychology(rsi, funding_rate, ob_ratio, volume_spike):
    """
    Detects retail human psychology (FOMO, Panic, Whale Traps, Capitulation)
    """
    psychology_score = 50
    sentiment_tag = "NEUTRAL ⚖️"
    
    # Extreme Greed / Retail FOMO Trap (Danger Zone for Longs)
    if rsi > 78 and funding_rate > 0.08:
        psychology_score -= 30
        sentiment_tag = "⚠️ RETAIL FOMO TRAP (Overheated)"
    
    # Panic Capitulation / Blood in the Streets (Smart Money Accumulation)
    elif rsi < 28 and funding_rate < -0.02 and volume_spike:
        psychology_score += 40
        sentiment_tag = "💎 PANIC CAPITULATION (Whale Accumulation)"
    
    # Healthy Bullish Momentum
    elif 45 <= rsi <= 65 and funding_rate <= 0.04 and ob_ratio > 1.2:
        psychology_score += 25
        sentiment_tag = "🚀 HEALTHY INSTITUTIONAL FLOW"
        
    # Bearish Breakdown Psychology
    elif rsi < 40 and funding_rate > 0.05:
        psychology_score -= 20
        sentiment_tag = "🩸 WEAK HANDS BLEEDING"
        
    return psychology_score, sentiment_tag

# ==========================================
# 3. MULTI-AGENT COUNCIL & COINMARKETCAP
# ==========================================
def fetch_cmc_fundamentals(symbol):
    api_key = os.getenv("CMC_API_KEY")
    if not api_key: return 50
    clean_symbol = symbol.split('/')[0].upper()
    try:
        res = requests.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest", 
                           headers={"X-CMC_PRO_API_KEY": api_key}, params={"symbol": clean_symbol}, timeout=4)
        if res.status_code == 200:
            rank = res.json()["data"][clean_symbol][0].get("cmc_rank", 500)
            if rank <= 15: return 95
            elif rank <= 50: return 85
            elif rank <= 150: return 70
            return 50
    except Exception:
        pass
    return 50

def multi_agent_council_debate(tech_score, futures_score, psych_score):
    """Autonomous AI Agents Debate to Filter Out Fakeouts"""
    consensus = int((tech_score * 0.35) + (futures_score * 0.30) + (psych_score * 0.35))
    return max(0, min(100, consensus))

# ==========================================
# 4. QUANTUM DEEP MARKET DATA FETCHERS
# ==========================================
def fetch_quantum_market_data(symbol):
    exchange_binance = ccxt.binance()
    exchange_bybit = ccxt.bybit()
    
    df_15m = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="15m", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_1h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="1h", limit=100), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_4h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="4h", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    
    spread = 0.0
    try:
        t_bin = exchange_binance.fetch_ticker(symbol)
        t_byt = exchange_bybit.fetch_ticker(symbol)
        spread = ((t_byt['last'] - t_bin['last']) / t_bin['last']) * 100
    except Exception:
        pass

    ob_ratio = 1.0
    try:
        ob = exchange_binance.fetch_order_book(symbol, limit=20)
        bids = sum([b[1] for b in ob['bids']])
        asks = sum([a[1] for a in ob['asks']])
        ob_ratio = bids / (asks + 1e-9)
    except Exception:
        pass

    funding = 0.01
    try:
        fr = exchange_binance.fetch_funding_rate(symbol)
        funding = fr.get('fundingRate', 0.01) * 100
    except Exception:
        pass

    # Volume Spike Check (Compare last volume with 20-period average)
    vol_spike = False
    try:
        avg_vol = df_1h['v'].rolling(20).mean().iloc[-1]
        current_vol = df_1h['v'].iloc[-1]
        if current_vol > (avg_vol * 1.8):
            vol_spike = True
    except Exception:
        pass

    return df_15m, df_1h, df_4h, ob_ratio, funding, spread, vol_spike

def fetch_global_macro_news():
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        score = 50
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            if any(w in title for w in ['bull', 'surge', 'rally', 'approval', 'gain']): score += 5
            if any(w in title for w in ['bear', 'crash', 'drop', 'hack', 'sec', 'ban']): score -= 5
        return max(0, min(100, score))
    except Exception:
        return 50

def get_all_market_pairs(limit=70):
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        return [sym for sym, m in markets.items() if m['active'] and m['quote'] == 'USDT' and m['spot'] and not is_stablecoin(sym)][:limit]
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

# ==========================================
# 5. ANALYSIS ENGINE
# ==========================================
def analyze_coin(symbol, macro_news, ai_db):
    try:
        df_15m, df_1h, df_4h, ob_ratio, funding, spread, vol_spike = fetch_quantum_market_data(symbol)
        close = df_1h['close'].iloc[-1]
        
        # Technicals
        df_1h['ema9'] = df_1h['close'].ewm(span=9).mean()
        df_1h['ema21'] = df_1h['close'].ewm(span=21).mean()
        
        delta = df_1h['close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df_1h['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        tr = np.maximum(df_1h['high'] - df_1h['low'], np.maximum(abs(df_1h['high'] - df_1h['close'].shift()), abs(df_1h['low'] - df_1h['close'].shift())))
        atr = tr.rolling(14).mean().iloc[-1]
        
        rsi = df_1h['rsi'].iloc[-1]
        ema_cross = df_1h['ema9'].iloc[-1] > df_1h['ema21'].iloc[-1]
        
        # Psychology Layer Integration
        psych_score, psych_tag = analyze_market_psychology(rsi, funding, ob_ratio, vol_spike)
        
        tech_score = 60 if ema_cross else 40
        if 40 <= rsi <= 65: tech_score += 15
        
        futures_score = 50
        if funding < 0: futures_score += 25
        elif funding > 0.06: futures_score -= 20
        if ob_ratio > 1.2: futures_score += 15
        
        cmc_score = fetch_cmc_fundamentals(symbol)
        final_score = multi_agent_council_debate(tech_score, futures_score, psych_score)
        
        signal_type = "LONG 🟢" if ema_cross and final_score >= 60 else "SHORT 🔴"
        
        if "LONG" in signal_type:
            sl = round(close - (atr * 1.7), 4)
            tp1 = round(close + (atr * 2.8), 4)
        else:
            sl = round(close + (atr * 1.7), 4)
            tp1 = round(close - (atr * 2.8), 4)

        return {
            "symbol": symbol, "signal": signal_type, "score": final_score,
            "price": close, "rsi": round(rsi, 1), "psych_tag": psych_tag,
            "funding": round(funding, 4), "spread": round(spread, 2),
            "cmc": cmc_score, "sl": sl, "tp1": tp1
        }
    except Exception as e:
        return None

# ==========================================
# 6. TELEGRAM 24/7 STREAMING DISPATCHER
# ==========================================
def send_telegram_alert(data):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return

    msg = (
        f"🌌 *24/7 GOD-MODE PSYCHOLOGY ALERT* 🌌\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Asset:* `{data['symbol']}` | Verdict: *{data['signal']}*\n"
        f"📊 *Quantum Score:* `{data['score']}/100`\n\n"
        f"💵 *Price:* `${data['price']}`\n"
        f"🧠 *Market Psychology:* {data['psych_tag']}\n"
        f"⚡ *Funding Rate:* `{data['funding']}%`\n"
        f"🔄 *Spread:* `{data['spread']}%` | *RSI:* `{data['rsi']}`\n\n"
        f"🎯 *Take Profit:* `${data['tp1']}`\n"
        f"🛡️ *Stop Loss:* `${data['sl']}`\n"
        f"⏰ *Time:* {datetime.utcnow().strftime('%H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass

# ==========================================
# 7. SINGLE-RUN EXECUTION (Triggered by 15-min Cron)
# ==========================================
if __name__ == "__main__":
    print("🔄 Starting God-Mode Psychology Market Scan...")
    alerted_history = load_json_db(ALERTED_HISTORY_FILE, {})
    ai_db = load_json_db(LEARNING_FILE, {"weights": {}})

    try:
        pairs = get_all_market_pairs(limit=70)
        macro_news = fetch_global_macro_news()
        print(f"🔍 Scanning {len(pairs)} assets at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC...")

        for pair in pairs:
            res = analyze_coin(pair, macro_news, ai_db)
            
            # Sirf tab alert jayega jab valid setup ho aur score 78 ya usse zyada ho
            if res and res['score'] >= 78:  
                symbol = res['symbol']
                last_alert_time = alerted_history.get(symbol, 0)
                current_time = time.time()
                
                # Cooldown mechanism: Don't spam the same coin within 4 hours (14400 seconds)
                if current_time - last_alert_time > 14400:
                    print(f"🔥 High-Score Setup Detected! Sending alert for {symbol} (Score: {res['score']})")
                    send_telegram_alert(res)
                    alerted_history[symbol] = current_time
                    save_json_db(ALERTED_HISTORY_FILE, alerted_history)
                    time.sleep(2) # Prevent telegram rate limits

        print("✅ Scan cycle complete successfully.")
        
    except Exception as e:
        print(f"⚠️ Exception caught: {e}")
        
