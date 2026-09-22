import os

# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_NAME = "Crypto Master Scanner AI"
VERSION = "10.0"

# Target Scan Limits
MAX_COINS = 30
OHLCV_LIMIT = 220
HTTP_TIMEOUT = 15

# Exchange IDs
SPOT_EXCHANGES = ["binance", "okx", "bybit", "kucoin"]
FUTURES_EXCHANGES = ["binanceusdm", "okx", "bybit", "kucoin"]

# Stablecoins to exclude from market scanning
STABLECOINS = {
    "USDT", "USDC", "FDUSD", "DAI", "USDE", "USDS",
    "USDD", "TUSD", "USDP", "PYUSD", "USDG", "RLUSD",
    "EURC", "EURT", "USTC"
}

# CoinMarketCap API Configuration
CMC_BASE_URL = "https://pro-api.coinmarketcap.com/v1"
CMC_API_KEY = os.getenv("CMC_API_KEY", "")

# News RSS Feed Sources
RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://news.bitcoin.com/feed/",
    "https://www.theblock.co/rss.xml",
]

# Analysis Timeframes & Weights
TIMEFRAMES = ["15m", "1h", "4h", "1d"]
TF_WEIGHTS = {
    "15m": 0.15,
    "1h": 0.25,
    "4h": 0.35,
    "1d": 0.25
}

# Risk Management Settings
DEFAULT_ATR_CAP_PERCENT = 0.05  # Max 5% ATR limit for SL/TP calculations
SL_ATR_MULTIPLIER = 1.5
TP_ATR_MULTIPLIER = 3.0
