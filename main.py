import os
import requests
import json
import pandas as pd
import numpy as np
import ccxt
import feedparser
from datetime import datetime

# ==========================================
# 1. EXCLUDED STABLECOINS & FIAT LIST
# ==========================================
EXCLUDED_STABLES = [
    'USDT', 'USDC', 'FDUSD', 'DAI', 'TUSD', 'USDE', 'USDD', 
    'EUR', 'GBP', 'BUSD', 'PYUSD', 'USDP', 'GUSD', 'AEUR'
]

def is_stablecoin(symbol):
    base = symbol.split('/')[0].split(':')[0].upper()
    return base in EXCLUDED_STABLES

# ==========================================
# 2. NEURAL SELF-LEARNING & MEMORY CORE
# ==========================================
LEARNING_FILE = "ai_learning_data.json"

def load_ai_neural_matrix():
    if os.path.exists(LEARNING_FILE):
        try:
            with open(LEARNING_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Autonomous Quantum Neural Weights Matrix
    return {
        "neural_weights": {"tech": 0.30, "futures": 0.25, "agent_debate": 0.20, "cmc": 0.15, "spread": 0.10},
        "score_offsets": {},
        "history": {}
    }

def save_ai_neural_matrix(data):
    try:
        with open(LEARNING_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Neural Matrix Sync Error: {e}")

def neural_reinforcement_learning(symbol, current_price, ai_db):
    """Self-Optimizing Neural Adjustment based on Past Target/SL Hit"""
    history = ai_db.get("history", {})
    offsets = ai_db.get("score_offsets", {})
    
    if symbol in history:
        last = history[symbol]
        tp1, sl = last.get("tp1", 0), last.get("sl", 0)
        signal = last.get("signal", "LONG 🟢")
        
        if "LONG" in signal:
            if tp1 > 0 and current_price >= tp1:
                offsets[symbol] = min(30, offsets.get(symbol, 0) + 6)
            elif sl > 0 and current_price <= sl:
                offsets[symbol] = max(-30, offsets.get(symbol, 0) - 6)
        else:
            if tp1 > 0 and current_price <= tp1:
                offsets[symbol] = min(30, offsets.get(symbol, 0) + 6)
            elif sl > 0 and current_price >= sl:
                offsets[symbol] = max(-30, offsets.get(symbol, 0) - 6)

    ai_db["score_offsets"] = offsets
    return ai_db

# ==========================================
# 3. COINMARKETCAP FUNDAMENTALS
# ==========================================
def fetch_cmc_fundamentals(symbol):
    api_key = os.getenv("CMC_API_KEY")
    if not api_key:
        return 50
    clean_symbol = symbol.split('/')[0].upper()
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    try:
        res = requests.get(url, headers={"X-CMC_PRO_API_KEY": api_key}, params={"symbol": clean_symbol}, timeout=4)
        if res.status_code == 200:
            rank = res.json()["data"][clean_symbol][0].get("cmc_rank", 500)
            if rank <= 15: return 95
            elif rank <= 50: return 85
            elif rank <= 150: return 70
            return 50
    except Exception:
        pass
    return 50

# ==========================================
# 4. MULTI-AGENT DEBATE ENGINE (THE COUNCIL)
# ==========================================
def multi_agent_council_debate(tech_score, futures_score, rsi, funding_rate, ob_ratio):
    """Autonomous AI Agents Debate to Filter Out Fakeouts"""
    bull_agent_score = tech_score
    bear_agent_risk = 0
    
    # Bullish Agent perspective
    if rsi < 35: bull_agent_score += 15
    if ob_ratio > 1.3: bull_agent_score += 15
    
    # Bearish / Risk Agent perspective
    if funding_rate > 0.08: bear_agent_risk += 25 # Overleveraged Long danger
    elif funding_rate < -0.05: bear_agent_risk -= 15 # Short squeeze bonus
    
    # Quant Judge Consensus Verdict
    consensus_score = int((bull_agent_score * 0.65) - (bear_agent_risk * 0.35))
    return max(0, min(100, consensus_score))

# ==========================================
# 5. QUANTUM MARKET DATA FETCHERS
# ==========================================
def fetch_quantum_market_data(symbol):
    exchange_binance = ccxt.binance()
    exchange_bybit = ccxt.bybit()
    
    # Multi-Timeframe Matrix (15m, 1h, 4h)
    df_15m = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="15m", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_1h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="1h", limit=100), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    df_4h = pd.DataFrame(exchange_binance.fetch_ohlcv(symbol, timeframe="4h", limit=50), columns=['t', 'o', 'h', 'l', 'c', 'v'])
    
    # Cross-Exchange Spread Arbitrage
    spread = 0.0
    try:
        t_bin = exchange_binance.fetch_ticker(symbol)
        t_byt = exchange_bybit.fetch_ticker(symbol)
        spread = ((t_byt['last'] - t_bin['last']) / t_bin['last']) * 100
    except Exception:
        pass

    # Orderbook Wall & Funding Rates
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

    return df_15m, df_1h, df_4h, ob_ratio, funding, spread

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

def get_all_market_pairs(limit=80):
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        return [sym for sym, m in markets.items() if m['active'] and m['quote'] == 'USDT' and m['spot'] and not is_stablecoin(sym)][:limit]
    except Exception:
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

# ==========================================
# 6. GOD-MODE QUANT ANALYSIS ENGINE
# ==========================================
def analyze_coin(symbol, macro_news, ai_db):
    try:
        df_15m, df_1h, df_4h, ob_ratio, funding, spread = fetch_quantum_market_data(symbol)
        close = df_1h['close'].iloc[-1]
        
        ai_db = neural_reinforcement_learning(symbol, close, ai_db)
        
        # Technical Calculations
        df_1h['ema9'] = df_1h['close'].ewm(span=9).mean()
        df_1h['ema21'] = df_1h['close'].ewm(span=21).mean()
        
        delta = df_1h['close'].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        df_1h['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        
        tr = np.maximum(df_1h['high'] - df_1h['low'], np.maximum(abs(df_1h['high'] - df_1h['close'].shift()), abs(df_1h['low'] - df_1h['close'].shift())))
        atr = tr.rolling(14).mean().iloc[-1]
        
        # Macro Regime (4H Trend)
        df_4h['ema50'] = df_4h['close'].ewm(span=50).mean()
        df_4h['ema200'] = df_4h['close'].ewm(span=200).mean()
        macro_bull = df_4h['ema50'].iloc[-1] > df_4h['ema200'].iloc[-1]
        
        # Sub-Scores
        tech_score = 50
        rsi = df_1h['rsi'].iloc[-1]
        ema_cross = df_1h['ema9'].iloc[-1] > df_1h['ema21'].iloc[-1]
        
        if ema_cross: tech_score += 20
        if 40 <= rsi <= 65: tech_score += 15
        elif rsi < 30: tech_score += 25
        
        futures_score = 50
        if funding < 0: futures_score += 25
        elif funding > 0.06: futures_score -= 20
        if ob_ratio > 1.2: futures_score += 15
        
        # Run Multi-Agent Debate
        agent_score = multi_agent_council_debate(tech_score, futures_score, rsi, funding, ob_ratio)
        cmc_score = fetch_cmc_fundamentals(symbol)
        spread_score = int(50 + (spread * 10))
        
        signal_type = "LONG 🟢" if ema_cross and macro_bull and agent_score > 50 else "SHORT 🔴"
        
        # Neural Matrix Matrix Multiplication Weighting
        w = ai_db.get("neural_weights", {"tech": 0.30, "futures": 0.25, "agent_debate": 0.20, "cmc": 0.15, "spread": 0.10})
        neural_offset = ai_db.get("score_offsets", {}).get(symbol, 0)
        
        composite = (
            (tech_score * w["tech"]) + 
            (futures_score * w["futures"]) + 
            (agent_score * w["agent_debate"]) + 
            (cmc_score * w["cmc"]) + 
            (spread_score * w["spread"]) + 
            neural_offset
        )
        score = max(1, min(99, int(composite)))

        # Dynamic Quantum Risk Management (ATR Dynamic Target & SL)
        if "LONG" in signal_type:
            sl = round(close - (atr * 1.7), 4)
            tp1 = round(close + (atr * 2.8), 4)
        else:
            sl = round(close + (atr * 1.7), 4)
            tp1 = round(close - (atr * 2.8), 4)

        ai_db.setdefault("history", {})[symbol] = {
            "signal": signal_type, "price": close, "tp1": tp1, "sl": sl
        }

        return {
            "symbol": symbol, "signal": signal_type, "score": score,
            "price": close, "rsi": round(rsi, 1), "ob_ratio": round(ob_ratio, 2),
            "funding": round(funding, 4), "spread": round(spread, 2),
            "cmc": cmc_score, "agent_score": agent_score, "sl": sl, "tp1": tp1
        }, ai_db

    except Exception as e:
        print(f"Skipping {symbol} due to anomaly: {e}")
        return None, ai_db

# ==========================================
# 7. TELEGRAM GOD-MODE DISPATCHER
# ==========================================
def send_god_mode_telegram(data):
    token, chat_id = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id: return

    score = data['score']
    tier = "🌌 GOD-MODE ALPHA" if score >= 80 else ("🔥 HIGH CONVICTION" if score >= 65 else "⚖️ NEUTRAL/WATCH")

    msg = (
        f"⚡ *GOD-MODE QUANTUM MASTER AI* ⚡\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Asset:* `{data['symbol']}` | Verdict: *{data['signal']}*\n"
        f"📊 *Quantum Score:* `{score}/100` | Tier: {tier}\n\n"
        f"💵 *Price:* `${data['price']}`\n"
        f"🤖 *AI Agent Council Score:* `{data['agent_score']}/100`\n"
        f"⚡ *Funding Rate:* `{data['funding']}%`\n"
        f"🔄 *Exchanges Spread:* `{data['spread']}%`\n"
        f"🏛️ *CMC Fundamental:* `{data['cmc']}/100`\n"
        f"📈 *RSI:* `{data['rsi']}` | *Buy Wall:* `{data['ob_ratio']}`\n\n"
        f"🎯 *Take Profit 1:* `${data['tp1']}`\n"
        f"🛡️ *Dynamic Stop Loss:* `${data['sl']}`\n"
        f"⏰ *Scan Time:* {datetime.utcnow().strftime('%H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)

# ==========================================
# 8. EXECUTION PIPELINE
# ==========================================
if __name__ == "__main__":
    ai_db = load_ai_neural_matrix()
    pairs = get_all_market_pairs(limit=80)
    macro_news = fetch_global_macro_news()
    results = []

    print("🌌 Initializing God-Mode Autonomous Quantum Pipeline...")
    for pair in pairs:
        res, ai_db = analyze_coin(pair, macro_news, ai_db)
        if res: results.append(res)

    save_ai_neural_matrix(ai_db)

    if results:
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        pd.DataFrame(results).to_csv("crypto_scan_results.csv", index=False)
        print("💾 Quantum State & CSV Artifact Saved.")

        print("📲 Broadcasting God-Mode Signals to Telegram...")
        for coin in results[:10]:
            send_god_mode_telegram(coin)
