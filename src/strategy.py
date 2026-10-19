def find_fvg(candles, touch_time, direction):
    """
    Find a three-candle Fair Value Gap after the H1 level is touched.

    candles: list of dictionaries containing time, high, and low.
    direction: "BUY" or "SELL".
    """
    results = []

    for i in range(2, len(candles)):
        first = candles[i - 2]
        third = candles[i]

        if first["time"] < touch_time:
            continue

        if direction == "SELL" and first["low"] > third["high"]:
            results.append({
                "direction": "SELL",
                "time": third["time"],
                "zone_low": third["high"],
                "zone_high": first["low"],
            })

        elif direction == "BUY" and first["high"] < third["low"]:
            results.append({
                "direction": "BUY",
                "time": third["time"],
                "zone_low": first["high"],
                "zone_high": third["low"],
            })

    return results
