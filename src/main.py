from datetime import timedelta

from data import fetch_h1, fetch_m3
from strategy import find_fvg
from notify import send_alarm


def main():
    print("Fetching gold price data...")

    h1 = fetch_h1()
    m3 = fetch_m3()

    if len(h1) < 2 or len(m3) < 3:
        print("Not enough candle data yet.")
        return

    ref = h1.iloc[-2]
    ref_time = h1.index[-2]
    next_hour = ref_time + timedelta(hours=1)

    window = m3[
        (m3.index >= next_hour)
        & (m3.index < next_hour + timedelta(hours=1))
    ]

    if len(window) < 4:
        print("Waiting for more M3 candles.")
        return

    closed = window.iloc[:-1]
    high = float(ref["High"])
    low = float(ref["Low"])

    checks = []

    high_touches = closed[closed["High"] >= high]
    low_touches = closed[closed["Low"] <= low]

    if not high_touches.empty:
        checks.append(("SELL", high_touches.index[0]))

    if not low_touches.empty:
        checks.append(("BUY", low_touches.index[0]))

    candles = [
        {
            "time": timestamp,
            "high": float(row["High"]),
            "low": float(row["Low"]),
        }
        for timestamp, row in closed.iterrows()
    ]

    for direction, touch_time in checks:
        setups = find_fvg(candles, touch_time, direction)

        if setups:
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
            print("Alert sent:", direction)

    print("Check completed.")


if --name-- == "--main--":
    main()
