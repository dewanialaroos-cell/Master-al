import math
import time
import requests
import feedparser
import ccxt
import pandas as pd
import numpy as np

import config

session = requests.Session()
session.headers.update({
    "User-Agent": "Crypto-Master-AI/10.0",
    "Accept": "application/json",
    "X-CMC_PRO_API_KEY": config.CMC_API_KEY
})

def number(value, default=np.nan):
    try:
        if value is None or value == "":
            return default
        val = float(value)
        return val if math.isfinite(val) else default
    except Exception:
        return default

def create_exchange(exchange_id, market_type):
    try:
        exchange_class = getattr(ccxt, exchange_id)
        options = {
            "enableRateLimit": True,
            "timeout": 15000,
            "options": {"defaultType": market_type}
        }
        exchange = exchange_class(options)
        exchange.load_markets()
        return exchange
    except Exception as e:
        print(f"Failed to load {exchange_id}: {e}")
        return None

def build_exchange_instances():
    spot = [(e_id, ex) for e_id in config.SPOT_EXCHANGES if (ex := create_exchange(e_id, "spot"))]
    futures = [(e_id, ex) for e_id in config.FUTURES_EXCHANGES if (ex := create_exchange(e_id, "swap"))]
    return spot, futures

def discover_candidates(spot_exchanges):
    markets = {}
    for exchange_id, exchange in spot_exchanges:
        try:
            tickers = exchange.fetch_tickers()
            for symbol, ticker in tickers.items():
                market = exchange.markets.get(symbol)
                if not market or not market.get("spot") or market.get("quote") != "USDT":
                    continue

                base = market.get("base")
                if not base or base.upper() in config.STABLECOINS:
                    continue

                base = base.upper()
                last = number(ticker.get("last"))
                quote_vol = number(ticker.get("quoteVolume"))

                if not math.isfinite(quote_vol):
                    base_vol = number(ticker.get("baseVolume"))
                    quote_vol = base_vol * last if (math.isfinite(base_vol) and math.isfinite(last)) else 0

                if quote_vol <= 0:
                    continue

                pair = f"{base}/USDT"
                if pair not in markets:
                    markets[pair] = {"symbol": pair, "market_volume": 0.0, "exchanges": {}}

                markets[pair]["market_volume"] += quote_vol
                markets[pair]["exchanges"][exchange_id] = quote_vol
        except Exception as e:
            print(f"Error in discovery on {exchange_id}: {e}")

    results = []
    for item in markets.values():
        if item["market_volume"] < 250000:
            continue
        results.append({
            "symbol": item["symbol"],
            "market_volume": round(item["market_volume"], 2),
            "exchange_count": len(item["exchanges"]),
            "exchanges": ",".join(item["exchanges"].keys())
        })

    results.sort(key=lambda x: x["market_volume"], reverse=True)
    return results[:config.MAX_COINS]

def fetch_ohlcv_data(exchange, symbol, timeframe):
    try:
        candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=config.OHLCV_LIMIT)
        if not candles or len(candles) < 60:
            return None
        df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna().reset_index(drop=True)
    except Exception:
        return None

def fetch_news():
    news = []
    for feed_url in config.RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:25]:
                title = getattr(entry, "title", "").strip()
                summary = getattr(entry, "summary", "").strip()
                if title:
                    news.append({"title": title, "summary": summary})
        except Exception as e:
            print(f"Error reading news feed {feed_url}: {e}")

    seen = set()
    unique_news = []
    for item in news:
        k = item["title"].lower()
        if k not in seen:
            seen.add(k)
            unique_news.append(item)
    return unique_news
