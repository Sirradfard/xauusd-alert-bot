from datetime import timedelta

import pandas as pd

from data import fetch_h1, fetch_m3
from strategy import find_fvg
from notify import send_alarm


def main():
    h1 = fetch_h1()
    m3 = fetch_m3()

    if len(h1) < 2 or len(m3) < 3:
        print("Not enough candle data yet.")
        return

    # Use the last completed H1 candle as the reference.
    ref = h1.iloc[-2]
    ref_time = h1.index[-2]
    next_hour = ref_time + timedelta(hours=1)

    # Only use M3 candles inside the following H1 period.
    window = m3[(m3.index >= next_hour) & (m3.index < next_hour + timedelta(hours=1))]

    if len(window) < 3:
        print("Waiting for more M3 candles.")
        return

    # Exclude the latest potentially incomplete M3 candle.
    closed = window.iloc[:-1]

    high = float(ref["High"])
    low = float(ref["Low"])

    # Find the first completed candle that touches either H1 level.
    high_touches = closed[closed["High"] >= high]
    low_touches = closed[closed["Low"] <= low]

    checks = []

    if not high_touches.empty:
        checks.append(("SELL", high_touches.index[0]))

    if not low_touches.empty:
        checks.append(("BUY", low_touches.index[0]))

    for direction, touch_time in checks:
        candles = []

        for timestamp, row in closed.iterrows():
            candles.append({
                "time": timestamp,
                "high": float(row["High"]),
                "low": float(row["Low"]),
            })

        setups = find_fvg(candles, touch_time, direction)

        if not setups:
            continue

        setup = setups[0]

        send_alarm(
            direction=direction,
            ref_time=str(ref_time),
            ref_high=high,
            ref_low=low,
            touch_time=str(touch_time),
            zone_low=setup["zone_low"],
            zone_high=setup["zone_high"],
        )


if name == "main":
    main()
