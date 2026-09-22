import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np

import config
import fetchers
import analysis
import risk_management

def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting {config.PROJECT_NAME} v{config.VERSION}")

    spot_exchanges, futures_exchanges = fetchers.build_exchange_instances()
    if not spot_exchanges:
        print("Error: No spot exchanges could be initialized.")
        return

    candidates = fetchers.discover_candidates(spot_exchanges)
    print(f"Discovered {len(candidates)} high-volume candidates.")

    news_data = fetchers.fetch_news()
    results = []

    for item in candidates:
        symbol = item["symbol"]
        primary_exchange = spot_exchanges[0][1]

        df_1h = fetchers.fetch_ohlcv_data(primary_exchange, symbol, "1h")
        if df_1h is None:
            continue

        price = df_1h["close"].iloc[-1]
        tf_analysis = analysis.analyze_timeframe(df_1h)
        pa_score, pa_label = analysis.price_action(df_1h)
        bo_score, bo_label = analysis.breakout(df_1h)

        tech_raw = (tf_analysis["score"] * 28 + pa_score * 7 + bo_score * 7)
        tech_score = np.clip(50 + tech_raw, 0, 100)

        signal, long_s, short_s = risk_management.generate_signal(tech_score)
        sl, tp = risk_management.calculate_trade_levels(price, signal, tf_analysis["atr"])

        results.append({
            "symbol": symbol,
            "price": price,
            "signal": signal,
            "long_score": long_s,
            "short_score": short_s,
            "stop_loss": sl,
            "take_profit": tp,
            "rsi": tf_analysis["rsi"],
            "breakout": bo_label,
            "volume_24h": item["market_volume"]
        })

        print(f"-> {symbol}: Signal={signal} | Price={price} | SL={sl} | TP={tp}")

    if results:
        df_out = pd.DataFrame(results)
        df_out.to_csv("crypto_scan_results.csv", index=False)
        print("Scan finished! Results saved to 'crypto_scan_results.csv'")

if __name__ == "__main__":
    main()
  
