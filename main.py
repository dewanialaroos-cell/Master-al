import os
import requests
import json
import pandas as pd
import numpy as np
import ccxt
import feedparser
from datetime import datetime

# ==========================================
# 1. STABLECOINS & FIAT EXCLUSION FILTER
# ==========================================
EXCLUDED_STABLES = [
    'USDT', 'USDC', 'FDUSD', 'DAI', 'TUSD', 'USDE', 'USDD', 
    'EUR', 'GBP', 'BUSD', 'PYUSD', 'USDP', 'GUSD', 'AEUR'
]

def is_stablecoin(symbol):
    base = symbol.split('/')[0].split(':')[0].upper()
    return base in EXCLUDED_STABLES

# ==========================================
# 2. ADVANCED QUANT SELF-LEARNING ENGINE
# ==========================================
LEARNING_FILE = "ai_learning_data.json"

def load_ai_database():
    if os.path.exists(LEARNING_FILE):
        try:
            with open(LEARNING_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "weights": {"tech": 0.35, "futures": 0.25, "news": 0.15, "cmc": 0.15, "spread": 0.10},
        "score_offsets": {},
        "history": {}
    }

def save_ai_database(data):
    try:
        with open(LEARNING_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving AI database: {e}")

def tune_ai_weights(symbol, current_price, ai_db):
    history = ai_db.get("history", {})
    offsets = ai_db.get("score_offsets", {})
    
    if symbol in history:
        last = history[symbol]
        tp1, sl = last.get("tp1", 0), last.get("sl", 0)
        signal = last.get("signal", "LONG")
        
        if signal == "LONG 🟢":
            if tp1 > 0 and current_price >= tp1:
                offsets[symbol] = min(25, offsets.get(symbol, 0) + 5)
            elif sl > 0 and current_price <= sl:
                offsets[symbol] = max(-25, offsets.get(symbol, 0) - 5)
        else: # SHORT
            if tp1 > 0 and current_price <= tp1:
                offsets[symbol] = min(25, offsets.get(symbol, 0) + 5)
            elif sl > 0 and current_price >= sl:
                offsets[symbol] = max(-25, offsets.get(symbol, 0) - 5)

    ai_db["score_offsets"] = offsets
    return ai_db

# ==========================================
# 3. FUNDAMENTALS (COINMARKETCAP API)
# ==========================================
def fetch_cmc_fundamentals(symbol):
    api_key = os.getenv("CMC_API_KEY")
    if not api_key:
        return 50
    clean_symbol = symbol.split('/')[0].upper()
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    headers = {"X-CMC_PRO_API_KEY": api_key}
    try:
        res = requests.get(url, headers=headers, params={"symbol": clean_symbol}, timeout=5)
        if res.status_code == 200:
            rank = res.json()["data"][clean_symbol][0].get("cmc_rank", 500)
            if rank <= 15: return 95
            elif rank <= 50: return 80
            elif rank <= 150: return 65
            return 45
    except Exception:
        pass
    return 50

# ==========================================
# 4. MULTI-EXCHANGE & DEEP MARKET DATA
# ==========================================
def fetch_deep_market_data(symbol):
    exchange_binance = ccxt.binance()
    exchange_bybit = ccxt.bybit()
    
    # 1. Multi-Timeframe Candles (15m, 1h, 4h)
    df_15m = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="15m", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_1h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="1h", limit=100), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_4h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="4h", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    
    # 2. Cross-Exchange Price Spread (Binance vs Bybit arbitrage check)
    price_spread = 0.0
    try:
        ticker_b = exchange_binance.fetch_ticker(symbol)
        ticker_by = exchange_bybit.fetch_ticker(symbol)
        price_spread = ((ticker_by['last'] - ticker_b['last']) / ticker_b['last']) * 100
    except Exception:
        pass

    # 3. Orderbook Wall & Funding Rates
    ob_ratio = 1.0
    try:
        ob = exchange_binance.fetch_order_book(symbol, limit=20)
        bids = sum([b[1] for b in ob['bids']])
        asks = sum([a[1] for a[1] for a in ob['asks']])
        ob_ratio = bids / (asks + 1e-9)
    except Exception:
        pass

    funding_rate = 0.01
    try:
        fr = exchange_binance.fetch_funding_rate(symbol)
        funding_rate = fr.get('fundingRate', 0.01) * 100
    except Exception:
        pass

    return df_15m, df_1h, df_4h, ob_ratio, funding_rate, price_spread

def fetch_news_sentiment():
    try:
        feed = feedparser.parse("https://cointelegraph.com/rss")
        bull = ['bull', 'surge', 'breakout', 'rally', 'adoption', 'approval', 'gain']
        bear = ['bear', 'crash', 'drop', 'hack', 'sec', 'ban', 'decline']
        score = 50
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            if any(w in title for w in bull): score += 5
            if any(w in title for w in bear): score -= 5
        return max(0, min(100, score))
    except Exception:
        return 50

def get_all_market_pairs(limit=80):
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        pairs = []
        for sym, m in markets.items():
            if m['active'] and m['quote'] == 'USDT' and m['spot']:
                if not is_stablecoin(sym):
                    pairs.append(sym)
        return pairs[:limit]
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

# ==========================================
# 5. QUANT ENGINE & ANALYSIS
# ==========================================
def analyze_coin(symbol, global_news, ai_db):
    try:
        df_15m, df_1h, df_4h, ob_ratio, funding_rate, price_spread = fetch_deep_market_data(symbol)
        close = df_1h['close'].iloc[-1]
        
        ai_db = tune_ai_weights(symbol, close, ai_db)
        
        # Indicators (1H & 15M)
        df_1h['ema9'] = df_1h['close'].ewm(span=9).mean()
        df_1h['ema21'] = df_1h['close'].ewm(span=21).mean()
        
        delta = df_1h['close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df_1h['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        tr = np.maximum(df_1h['high'] - df_1h['low'], np.maximum(abs(df_1h['high'] - df_1h['close'].shift()), abs(df_1h['low'] - df_1h['close'].shift())))
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Multi-TF Macro Regime (4H)
        df_4h['ema50'] = df_4h['close'].ewm(span=50).mean()
        df_4h['ema200'] = df_4h['close'].ewm(span=200).mean()
        macro_bull = df_4h['ema50'].iloc[-1] > df_4h['ema200'].iloc[-1]
        
        # Scoring Modules
        tech_score = 50
        rsi = df_1h['rsi'].iloc[-1]
        ema_cross = df_1h['ema9'].iloc[-1] > df_1h['ema21'].iloc[-1]
        
        if ema_cross: tech_score += 20
        if 40 <= rsi <= 65: tech_score += 15
        elif rsi < 30: tech_score += 25
        
        futures_score = 50
        if funding_rate < 0: futures_score += 25
        elif funding_rate > 0.05: futures_score -= 15
        if ob_ratio > 1.2: futures_score += 15
        
        cmc_score = fetch_cmc_fundamentals(symbol)
        spread_score = int(50 + (price_spread * 10)) # Arbitrage weight adjustment
        
        signal_type = "LONG 🟢" if ema_cross and macro_bull else "SHORT 🔴"
        
        w = ai_db.get("weights", {"tech": 0.35, "futures": 0.25, "news": 0.15, "cmc": 0.15, "spread": 0.10})
        offset = ai_db.get("score_offsets", {}).get(symbol, 0)
        
        composite = (
            (tech_score * w["tech"]) + 
            (futures_score * w["futures"]) + 
            (global_news * w["news"]) + 
            (cmc_score * w["cmc"]) + 
            (spread_score * w["spread"]) + 
            offset
        )
        score = max(1, min(99, int(composite)))

        # Dynamic Kelly Risk / SL & TP
        if signal_type == "LONG 🟢":
            sl = round(close - (atr * 1.8), 4)
            tp1 = round(close + (atr * 2.8), 4)
        else:
            sl = round(close + (atr * 1.8), 4)
            tp1 = round(close - (atr * 2.8), 4)

        ai_db.setdefault("history", {})[symbol] = {
            "signal": signal_type, "price": close, "tp1": tp1, "sl": sl
        }

        return {
            "symbol": symbol, "signal": signal_type, "score": score,
            "price": close, "rsi": round(rsi, 1), "ob_ratio": round(ob_ratio, 2),
            "funding": round(funding_rate, 4), "spread": round(price_spread, 2),
            "cmc": cmc_score, "news": global_news, "sl": sl, "tp1": tp1
        }, ai_db

    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None, ai_db

# ==========================================
# 6. TELEGRAM ALERT SYSTEM
# ==========================================
def send_telegram(data):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return

    score = data['score']
    status = "🔥 ELITE SETUP" if score >= 75 else ("⚖️ WATCHLIST" if score >= 50 else "⚠️ AVOID")

    msg = (
        f"🌌 *QUANTUM QUANT MASTER AI REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Asset:* `{data['symbol']}` | Action: *{data['signal']}*\n"
        f"📊 *Master Score:* `{score}/100` | Status: {status}\n\n"
        f"💵 *Price:* `${data['price']}`\n"
        f"⚡ *Funding Rate:* `{data['funding']}%`\n"
        f"🔄 *Exchanges Spread:* `{data['spread']}%`\n"
        f"🏛️ *CMC Fund Score:* `{data['cmc']}/100`\n"
        f"📈 *RSI:* `{data['rsi']}` | *Buy Wall:* `{data['ob_ratio']}`\n\n"
        f"🎯 *Take Profit 1:* `${data['tp1']}`\n"
        f"🛡️ *Dynamic Stop Loss:* `${data['sl']}`\n"
        f"⏰ *Time:* {datetime.utcnow().strftime('%H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)

# ==========================================
# 7. MAIN PIPELINE
# ==========================================
if __name__ == "__main__":
    ai_db = load_ai_database()
    pairs = get_all_market_pairs(limit=80)
    news = fetch_news_sentiment()
    results = []

    print("🚀 Initializing Quantum Multi-Exchange Pipeline...")
    for pair in pairs:
        res, ai_db = analyze_coin(pair, news, ai_db)
        if res: results.append(res)

    save_ai_database(ai_db)

    if results:
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        pd.DataFrame(results).to_csv("crypto_scan_results.csv", index=False)
        print("💾 Artifact CSV Saved.")

        print("📲 Broadcasting Elite Telegram Signals...")
        for coin in results[:10]:
            send_telegram(coin)
