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
    'EUR', 'GBP', 'BUSD', 'PYUSD', 'USDP', 'GUSD', 'AEUR', 'TUSD'
]

def is_stablecoin(symbol):
    """Check if the pair contains any stablecoin base currency"""
    base = symbol.split('/')[0].split(':')[0].upper()
    return base in EXCLUDED_STABLES

# ==========================================
# 2. FETCH ALL ACTIVE CRYPTO MARKET PAIRS
# ==========================================
def fetch_all_market_pairs(limit_market=100):
    """Fetch all active USDT trading pairs from Exchange dynamically"""
    try:
        exchange = ccxt.binance()
        markets = exchange.load_markets()
        
        usdt_pairs = []
        for symbol, market in markets.items():
            if market['active'] and market['quote'] == 'USDT' and market['spot']:
                if not is_stablecoin(symbol):
                    usdt_pairs.append(symbol)
                    
        print(f"Total non-stablecoin crypto pairs discovered: {len(usdt_pairs)}")
        # Scan top active volume coins up to limit
        return usdt_pairs[:limit_market]
    except Exception as e:
        print(f"Error fetching markets: {e}")
        # Fallback list if exchange network call limits
        return ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT", "ADA/USDT", "AVAX/USDT", "DOGE/USDT", "NEAR/USDT", "LINK/USDT"]

# ==========================================
# 3. DATA FETCHERS (A to Z MARKET DATA)
# ==========================================
def fetch_binance_data(symbol, timeframe="1h", limit=100):
    """Fetch OHLCV & Order Book Pressure from Exchange"""
    exchange = ccxt.binance()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    
    try:
        order_book = exchange.fetch_order_book(symbol, limit=20)
        bids_vol = sum([bid[1] for bid in order_book['bids']])
        asks_vol = sum([ask[1] for ask in order_book['asks']])
        order_book_ratio = bids_vol / (asks_vol + 1e-9)
    except Exception:
        order_book_ratio = 1.0

    return df, order_book_ratio

def fetch_crypto_news_sentiment():
    """Scan Live Crypto News RSS Feed"""
    try:
        feed_url = "https://cointelegraph.com/rss"
        feed = feedparser.parse(feed_url)
        bullish_keywords = ['bull', 'surge', 'breakout', 'rally', 'adoption', 'approval', 'gain']
        bearish_keywords = ['bear', 'crash', 'drop', 'hack', 'sec', 'ban', 'decline']
        
        sentiment_score = 50
        for entry in feed.entries[:10]:
            title = entry.title.lower()
            if any(w in title for w in bullish_keywords):
                sentiment_score += 5
            if any(w in title for w in bearish_keywords):
                sentiment_score -= 5
                
        return max(0, min(100, sentiment_score))
    except Exception:
        return 50

def get_ai_learning_offset(symbol):
    """Retrieve self-learning performance adjustment"""
    file_path = "ai_learning_data.json"
    if os.path.exists(file_path):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                return data.get("score_offsets", {}).get(symbol, 0)
        except Exception:
            return 0
    return 0

# ==========================================
# 4. ANALYSIS ENGINE
# ==========================================
def analyze_coin(symbol, global_news_score):
    try:
        df, ob_ratio = fetch_binance_data(symbol)
        close = df['close'].iloc[-1]
        
        # EMA
        df['ema9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1)))
        )
        atr = df['tr'].rolling(14).mean().iloc[-1]
        
        # Score Engine
        tech_score = 50
        rsi_val = df['rsi'].iloc[-1]
        
        if df['ema9'].iloc[-1] > df['ema21'].iloc[-1]: tech_score += 15
        if 40 <= rsi_val <= 65: tech_score += 15
        elif rsi_val < 30: tech_score += 20 # Oversold Bonus
        if ob_ratio > 1.2: tech_score += 10 # Buy wall advantage

        ai_offset = get_ai_learning_offset(symbol)
        final_score = int((tech_score * 0.6) + (global_news_score * 0.4) + ai_offset)
        final_score = max(1, min(99, final_score))

        sl = round(close - (atr * 1.5), 4)
        tp1 = round(close + (atr * 2.0), 4)

        return {
            "symbol": symbol,
            "score": final_score,
            "price": close,
            "rsi": round(rsi_val, 1),
            "ob_ratio": round(ob_ratio, 2),
            "news_score": global_news_score,
            "sl": sl,
            "tp1": tp1
        }
    except Exception as e:
        print(f"Skipping {symbol} due to scan error: {e}")
        return None

# ==========================================
# 5. TELEGRAM ALERT DISPATCHER
# ==========================================
def send_telegram_report(coin_data):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram Secrets Missing!")
        return

    score = coin_data['score']
    if score >= 70:
        status = "🟢 STRONG BUY (High Potential)"
    elif score >= 50:
        status = "🟡 NEUTRAL / WATCHLIST"
    else:
        status = "🔴 LOW SCORE / AVOID"

    message = (
        f"🤖 *MASTER AI 360° SCAN REPORT*\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Coin:* `{coin_data['symbol']}`\n"
        f"📊 *Master AI Score:* `{score}/100`\n"
        f"🚦 *Status:* {status}\n\n"
        f"💵 *Current Price:* `${coin_data['price']}`\n"
        f"📈 *RSI Level:* `{coin_data['rsi']}`\n"
        f"⚖️ *Buy/Sell Wall Ratio:* `{coin_data['ob_ratio']}`\n"
        f"📰 *News Sentiment:* `{coin_data['news_score']}/100`\n\n"
        f"🎯 *Take Profit 1:* `${coin_data['tp1']}`\n"
        f"🛡️ *Stop Loss:* `${coin_data['sl']}`\n"
        f"⏰ *Scan Time:* {datetime.utcnow().strftime('%H:%M UTC')}\n"
        f"━━━━━━━━━━━━━━━━━━━"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram post error: {e}")

# ==========================================
# 6. MAIN EXECUTION LOOP
# ==========================================
if __name__ == "__main__":
    print("Fetching entire crypto market pairs...")
    # Full Market Fetch (Scans top 80 market dynamic coins excluding all stables)
    all_pairs = fetch_all_market_pairs(limit_market=80)
    
    global_news = fetch_crypto_news_sentiment()
    results = []

    print(f"Scanning market coins...")
    for pair in all_pairs:
        res = analyze_coin(pair, global_news)
        if res:
            results.append(res)

    if results:
        # Sort results by Master AI Score in descending order
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Save complete market CSV artifact
        df_out = pd.DataFrame(results)
        df_out.to_csv("crypto_scan_results.csv", index=False)
        print("Market CSV Saved successfully.")

        # Send Telegram updates for Top Analyzed Coins
        print("Broadcasting Telegram Alerts for Scanned Coins...")
        for top_coin in results[:10]: # Top 10 High/Low Ranked Signals broadcasted
            send_telegram_report(top_coin)
