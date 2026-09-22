import math
from datetime import datetime, timezone
import pandas as pd
import numpy as np

import config
import fetchers
import analysis
import risk_management
import ai_learning


def main():
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting {config.PROJECT_NAME} v{config.VERSION}")

    # 1. Exchange instances initialize karein
    spot_exchanges, futures_exchanges = fetchers.build_exchange_instances()
    if not spot_exchanges:
        print("Error: No spot exchanges available.")
        return

    # 2. High volume crypto candidates find karein
    candidates = fetchers.discover_candidates(spot_exchanges)
    print(f"Discovered {len(candidates)} high-volume candidates.")

    # 3. Latest crypto news fetch karein
    news_data = fetchers.fetch_news()
    results = []
    price_map = {}

    # 4. Target candidates ko analyze karein
    for item in candidates:
        symbol = item["symbol"]
        primary_exchange = spot_exchanges[0][1]

        df_1h = fetchers.fetch_ohlcv_data(primary_exchange, symbol, "1h")
        if df_1h is None:
            continue

        price = df_1h["close"].iloc[-1]
        price_map[symbol] = price

        # Indicators & Technical Analysis
        tf_analysis = analysis.analyze_timeframe(df_1h)
        pa_score, pa_label = analysis.price_action(df_1h)
        bo_score, bo_label = analysis.breakout(df_1h)

        # AI Self Learning Adjustment Multiplier
        learning_adj = ai_learning.get_learning_multiplier(symbol)

        # Base technical score with AI learning factor
        tech_raw = (tf_analysis["score"] * 28 + pa_score * 7 + bo_score * 7)
        tech_score = np.clip((50 + tech_raw) * (1 + learning_adj), 0, 100)

        # Generate signal & trade levels
        signal, long_s, short_s = risk_management.generate_signal(tech_score)
        sl, tp = risk_management.calculate_trade_levels(price, signal, tf_analysis["atr"])

        # Active trade signal record karein (for self-learning tracking)
        if signal != "NO TRADE":
            ai_learning.record_signal(symbol, signal, price, sl, tp)

        results.append({
            "symbol": symbol,
            "price": price,
            "signal": signal,
            "long_score": long_s,
            "short_score": short_s,
            "stop_loss": sl,
            "take_profit": tp,
            "learning_adjustment": f"{learning_adj * 100:.1f}%",
            "rsi": tf_analysis["rsi"],
            "breakout": bo_label,
            "volume_24h": item["market_volume"]
        })

        print(f"-> {symbol}: Signal={signal} | Price={price} | SL={sl} | TP={tp} | AI Adj={learning_adj * 100:.1f}%")

    # 5. AI Self Learning - Purane signals ke outcomes check aur update karein
    try:
        ai_learning.update_signal_outcomes(price_map)
        print("AI Self-Learning database updated with latest prices.")
    except Exception as e:
        print(f"Error updating AI Learning outcomes: {e}")

    # 6. Results CSV file me export karein
    if results:
        df_out = pd.DataFrame(results)
        df_out.to_csv("crypto_scan_results.csv", index=False)
        print("Scan finished! Results saved to 'crypto_scan_results.csv'")


if __name__ == "__main__":
    main()
    
