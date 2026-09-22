import os
import json
from datetime import datetime, timezone

LEARNING_FILE = "ai_learning_data.json"

def load_learning_data():
    if os.path.exists(LEARNING_FILE):
        try:
            with open(LEARNING_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"history": [], "stats": {}}

def save_learning_data(data):
    try:
        with open(LEARNING_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving learning data: {e}")

def record_signal(symbol, signal, price, stop_loss, take_profit):
    if signal == "NO TRADE":
        return

    data = load_learning_data()
    entry = {
        "symbol": symbol,
        "signal": signal,
        "entry_price": price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "PENDING"
    }
    data["history"].append(entry)
    save_learning_data(data)

def update_signal_outcomes(current_prices):
    data = load_learning_data()
    updated = False

    for item in data["history"]:
        if item["status"] != "PENDING":
            continue

        symbol = item["symbol"]
        if symbol not in current_prices:
            continue

        curr_p = current_prices[symbol]
        sig = item["signal"]
        tp = item["take_profit"]
        sl = item["stop_loss"]

        # Check outcomes
        if sig == "LONG":
            if curr_p >= tp:
                item["status"] = "WIN"
                updated = True
            elif curr_p <= sl:
                item["status"] = "LOSS"
                updated = True
        elif sig == "SHORT":
            if curr_p <= tp:
                item["status"] = "WIN"
                updated = True
            elif curr_p >= sl:
                item["status"] = "LOSS"
                updated = True

    if updated:
        # Recalculate stats
        stats = {}
        for item in data["history"]:
            sym = item["symbol"]
            if sym not in stats:
                stats[sym] = {"wins": 0, "losses": 0}
            if item["status"] == "WIN":
                stats[sym]["wins"] += 1
            elif item["status"] == "LOSS":
                stats[sym]["losses"] += 1

        data["stats"] = stats
        save_learning_data(data)

def get_learning_multiplier(symbol):
    data = load_learning_data()
    stats = data.get("stats", {}).get(symbol)

    if not stats:
        return 0.0  # Neutral (no history)

    wins = stats.get("wins", 0)
    losses = stats.get("losses", 0)
    total = wins + losses

    if total < 3:
        return 0.0  # Not enough sample size

    win_rate = wins / total

    if win_rate >= 0.70:
        return 0.12   # +12% Confidence Boost
    elif win_rate >= 0.55:
        return 0.05   # +5% Confidence Boost
    elif win_rate <= 0.30:
        return -0.15  # -15% Confidence Penalty
    elif win_rate <= 0.45:
        return -0.05  # -5% Penalty

    return 0.0
              
