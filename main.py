import os
import time
import asyncio
import json
import requests
import pandas as pd
import numpy as np
import ccxt.pro as ccxtpro
import feedparser
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier

# ==========================================
# 1. QUANTUM EXCLUSIONS & CONFIGURATIONS
# ==========================================
EXCLUDED_STABLES = [
    'USDT', 'USDC', 'FDUSD', 'DAI', 'TUSD', 'USDE', 'USDD', 
    'EUR', 'GBP', 'BUSD', 'PYUSD', 'USDP', 'GUSD', 'AEUR'
]

def is_stablecoin(symbol):
    base = symbol.split('/')[0].split(':')[0].upper()
    return base in EXCLUDED_STABLES

LEARNING_FILE = "ai_quantum_mind.json"
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
# 2. CONTINUOUS LEARNING SWARM MIND
# ==========================================
def get_quantum_ai_mind():
    default_mind = {
        "generation": 1,
        "weights": {"tech": 0.20, "orderbook": 0.20, "sentiment": 0.20, "deep_lstm": 0.20, "psych": 0.20},
        "mutation_rate": 0.015,
        "historical_dataset": [],
        "neural_memory_stats": {"total_scans": 0, "total_wins": 0, "total_losses": 0, "evolution_score": 100}
    }
    return load_json_db(LEARNING_FILE, default_mind)

def log_every_scan_to_memory(ai_mind, feature_vector, outcome_label):
    dataset = ai_mind.setdefault("historical_dataset", [])
    dataset.append({"features": feature_vector, "success": outcome_label})
    if len(dataset) > 3000:
        ai_mind["historical_dataset"] = dataset[-3000:]
    ai_mind["neural_memory_stats"]["total_scans"] += 1
    save_json_db(LEARNING_FILE, ai_mind)

def deep_neural_sequence_prediction(df_closes):
    try:
        prices = df_closes.values[-20:]
        if len(prices) < 20: return 50
        gradients = np.gradient(prices)
        momentum_score = np.mean(gradients > 0) * 100
        return int(max(10, min(99, momentum_score)))
    except Exception:
        return 50

def predict_machine_learning_edge(ai_mind, current_features):
    dataset = ai_mind.get("historical_dataset", [])
    if len(dataset) < 10:
        return 50
    try:
        X = [d['features'] for d in dataset]
        y = [d['success'] for d in dataset]
        if len(set(y)) < 2:
            return 50
        clf = RandomForestClassifier(n_estimators=50, random_state=42)
        clf.fit(X, y)
        prob = clf.predict_proba([current_features])[0][1]
        return int(prob * 100)
    except Exception:
        return 50

# ==========================================
# 3. LEVEL-3 ORDER BOOK IMBALANCE ENGINE
# ==========================================
async def analyze_order_book_depth(exchange, symbol):
    try:
        order_book = await exchange.fetch_order_book(symbol, limit=20)
        bids = order_book.get('bids', [])
        asks = order_book.get('asks', [])
        
        if not bids or not asks: return 50
        
        bid_volume = sum([bid[1] for bid in bids])
        ask_volume = sum([ask[1] for ask in asks])
        
        total_volume = bid_volume + ask_volume
        if total_volume == 0: return 50
        
        imbalance_score = (bid_volume / total_volume) * 100
        return int(max(10, min(95, imbalance_score)))
    except Exception:
        return 50

# ==========================================
# 4. OMNISCIENT MACRO & SENTIMENT
# ==========================================
def scan_omniscient_macro_and_sentiment():
    sources = [
        "https://cointelegraph.com/rss",
        "https://coindesk.com/arc/outboundfeeds/rss/",
        "https://bitcoinmagazine.com/.rss/full/",
        "https://decrypt.co/feed"
    ]
    macro_score = 50
    sentiment_score = 50
    
    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:8]:
                title = entry.title.lower()
                if any(w in title for w in ['bull', 'surge', 'rally', 'approval', 'breakout', 'institutional', 'etf', 'reserve', 'adoption']): 
                    macro_score += 4
                    sentiment_score += 5
                if any(w in title for w in ['bear', 'crash', 'drop', 'hack', 'sec', 'ban', 'liquidation', 'lawsuit', 'fud']): 
                    macro_score -= 4
                    sentiment_score -= 5
        except Exception:
            pass
            
    try:
        fg_res = requests.get("https://api.alternative.me/fng/?limit=1", timeout=3).json()
        if "data" in fg_res:
            fg_val = int(fg_res["data"][0]["value"])
            sentiment_score = int((sentiment_score + fg_val) / 2)
    except Exception:
        pass

    return max(10, min(95, macro_score)), max(10, min(95, sentiment_score))

# ==========================================
# 5. LLM-POWERED COMMENTARY
# ==========================================
def generate_llm_market_commentary(symbol, signal, score, sentiment):
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return f"Demo Paper Testing AI: Asset {symbol} detected with {signal} trend configuration at directional strength of {score}%."
    
    try:
        headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
        prompt = f"Write a brief 2-sentence market evaluation for crypto asset {symbol} showing a {signal} trend with strength {score}%."
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": "You are a quantitative demo trading AI."}, {"role": "user", "content": prompt}],
            "max_tokens": 50
        }
        res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=5).json()
        return res["choices"][0]["message"]["content"].strip()
    except Exception:
        return f"Order book depth and momentum metrics indicate active {signal} bias for {symbol}."

def quantum_timeframe_matrix(df_15m, df_1h, df_4h):
    try:
        ema9_15 = df_15m['close'].ewm(span=9).mean().iloc[-1]
        ema21_15 = df_15m['close'].ewm(span=21).mean().iloc[-1]
        t15 = ema9_15 > ema21_15

        ema9_1h = df_1h['close'].ewm(span=9).mean().iloc[-1]
        ema21_1h = df_1h['close'].ewm(span=21).mean().iloc[-1]
        t1h = ema9_1h > ema21_1h

        ema9_4h = df_4h['close'].ewm(span=9).mean().iloc[-1]
        ema21_4h = df_4h['close'].ewm(span=21).mean().iloc[-1]
        t4h = ema9_4h > ema21_4h

        bull_count = sum([t15, t1h, t4h])
        if bull_count >= 2: return "BULLISH"
        return "BEARISH"
    except Exception:
        return "BULLISH"

# ==========================================
# 6. TELEGRAM DISPATCHER (PAPER TESTING MODE)
# ==========================================
def send_telegram_alert(data):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return

    msg = (
        f"🧪 *PAPER TESTING AI SIGNAL* 🧪\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Asset:* `{data['symbol']}`\n"
        f"🔮 *Direction:* *{data['signal']}*\n"
        f"📈 *Trend Conviction Strength:* `{data['score']}%`\n"
        f"🧬 *Total Scans Learned:* `{data['total_scans']}`\n\n"
        f"💵 *Current Price:* `${data['price']}`\n"
        f"🧱 *OrderBook Wall:* `{data['orderbook_score']}%` | *RSI:* `{data['rsi']}`\n\n"
        f"📝 *AI Intelligence Report:*\n_{data['commentary']}_\n\n"
        f"🎯 *Demo Target 1:* `${data['tp1']}`\n"
        f"🚀 *Demo Target 2:* `${data['tp2']}`\n"
        f"🛡️ *Demo Stop Loss:* `${data['sl']}`\n"
        f"⏰ *Time:* {datetime.utcnow().strftime('%H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception:
        pass

# ==========================================
# 7. ASYNCHRONOUS DEMO DAEMON ENGINE
# ==========================================
async def async_quantum_market_daemon():
    print("🧪 Booting Paper Testing Unfiltered AI Daemon...")
    ai_mind = get_quantum_ai_mind()
    
    exchange = ccxtpro.binance({'enableRateLimit': True})

    try:
        markets = await exchange.load_markets()
        pairs = [sym for sym, m in markets.items() if m['active'] and m['quote'] == 'USDT' and m['spot'] and not is_stablecoin(sym)]
        print(f"🔍 Loaded {len(pairs)} pairs for autonomous paper testing.")
    except Exception as e:
        print(f"⚠️ Market Load Error: {e}")
        await exchange.close()
        return

    alerted_history = load_json_db(ALERTED_HISTORY_FILE, {})

    while True:
        try:
            macro_news, sentiment_score = scan_omniscient_macro_and_sentiment()
            print(f"🔄 Executing Unfiltered Paper Scan at {datetime.utcnow().strftime('%H:%M:%S UTC')}...")

            sample_pairs = pairs[:20] # Scan top sample pairs every cycle
            
            for symbol in sample_pairs:
                try:
                    ohlcv_15m = await exchange.fetch_ohlcv(symbol, timeframe="15m", limit=50)
                    ohlcv_1h = await exchange.fetch_ohlcv(symbol, timeframe="1h", limit=100)
                    ohlcv_4h = await exchange.fetch_ohlcv(symbol, timeframe="4h", limit=50)
                    
                    if not ohlcv_1h or len(ohlcv_1h) < 30: continue
                    
                    df_15m = pd.DataFrame(ohlcv_15m, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    df_1h = pd.DataFrame(ohlcv_1h, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    df_4h = pd.DataFrame(ohlcv_4h, columns=['t', 'o', 'h', 'l', 'c', 'v'])
                    
                    close = df_1h['close'].iloc[-1]
                    trend_direction = quantum_timeframe_matrix(df_15m, df_1h, df_4h)
                    
                    delta = df_1h['close'].diff()
                    gain = delta.clip(lower=0).rolling(14).mean()
                    loss = (-delta.clip(upper=0)).rolling(14).mean()
                    df_1h['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
                    rsi = df_1h['rsi'].iloc[-1]

                    tr = np.maximum(df_1h['high'] - df_1h['low'], np.maximum(abs(df_1h['high'] - df_1h['close'].shift()), abs(df_1h['low'] - df_1h['close'].shift())))
                    atr = tr.rolling(14).mean().iloc[-1]

                    orderbook_score = await analyze_order_book_depth(exchange, symbol)
                    lstm_score = deep_neural_sequence_prediction(df_1h['close'])
                    
                    tech_score = 80 if trend_direction == "BULLISH" else 30
                    feature_vector = [float(rsi), float(macro_news), float(sentiment_score), float(orderbook_score), float(lstm_score)]
                    
                    scan_outcome_label = 1 if trend_direction == "BULLISH" else 0
                    log_every_scan_to_memory(ai_mind, feature_vector, scan_outcome_label)

                    ml_probability = predict_machine_learning_edge(ai_mind, feature_vector)

                    # Calculate dynamic strength percentage
                    strength_score = int((tech_score * 0.4) + (orderbook_score * 0.3) + (lstm_score * 0.3))
                    strength_score = max(15, min(98, strength_score))

                    signal_label = "BULLISH 🟢" if trend_direction == "BULLISH" else "BEARISH 🔴"

                    # NO RESTRICTIONS: Every evaluated trend now alerts immediately!
                    last_alert = alerted_history.get(symbol, 0)
                    current_time = time.time()
                    
                    # 1 hour cooldown per coin to avoid duplicate spam within the hour
                    if current_time - last_alert > 3600:
                        if "BULLISH" in signal_label:
                            sl = round(close - (atr * 1.5), 4)
                            tp1 = round(close + (atr * 2.0), 4)
                            tp2 = round(close + (atr * 4.0), 4)
                        else:
                            sl = round(close + (atr * 1.5), 4)
                            tp1 = round(close - (atr * 2.0), 4)
                            tp2 = round(close - (atr * 4.0), 4)

                        commentary = generate_llm_market_commentary(symbol, signal_label, strength_score, sentiment_score)

                        payload = {
                            "symbol": symbol, "signal": signal_label, "score": strength_score,
                            "price": close, "rsi": round(rsi, 1), "total_scans": ai_mind["neural_memory_stats"]["total_scans"],
                            "orderbook_score": orderbook_score, "sentiment": sentiment_score, 
                            "atr_val": round(atr, 4), "commentary": commentary, "sl": sl, "tp1": tp1, "tp2": tp2
                        }

                        print(f"🧪 Paper Test Alert Dispatched: {symbol} ({signal_label} - Strength: {strength_score}%)")
                        send_telegram_alert(payload)

                        alerted_history[symbol] = current_time
                        save_json_db(ALERTED_HISTORY_FILE, alerted_history)
                    
                    await asyncio.sleep(0.3)
                except Exception:
                    continue

            print("💤 Paper test scan cycle finished and logged.")
            break

        except Exception as e:
            print(f"⚠️ Daemon Exception: {e}")
            break

    await exchange.close()

if __name__ == "__main__":
    try:
        asyncio.run(async_quantum_market_daemon())
    except KeyboardInterrupt:
        print("🛑 Paper Daemon terminated.")
