import lzma
import struct
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests

BASE_URL = "https://datafeed.dukascopy.com/datafeed"


def fetch_day(day):
    url = (
        f"{BASE_URL}/XAUUSD/{day.year}/"
        f"{day.month - 1:02d}/{day.day:02d}/"
        "BID_candles_min_1.bi5"
    )

    response = requests.get(url, timeout=30)

    if response.status_code == 404:
        return []

    response.raise_for_status()

    if not response.content:
        return []

    raw = lzma.decompress(response.content, format=lzma.FORMAT_ALONE)
    rows = []

    for offset in range(0, len(raw), 24):
        chunk = raw[offset:offset + 24]

        if len(chunk) != 24:
            continue

        seconds, open_, close, low, high, volume = struct.unpack(
            ">IIIIIf", chunk
        )

        rows.append({
            "Time": day + timedelta(seconds=seconds),
            "Open": open_ / 1000,
            "High": high / 1000,
            "Low": low / 1000,
            "Close": close / 1000,
        })

    return rows


def fetch_candles(days):
    end = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = end - timedelta(days=days)
    rows = []
    day = start

    while day <= end:
        rows.extend(fetch_day(day))
        day += timedelta(days=1)

    if not rows:
        raise RuntimeError("Dukascopy returned no gold candles")

    data = pd.DataFrame(rows)
    data["Time"] = pd.to_datetime(data["Time"], utc=True)
    data = data.set_index("Time").sort_index()
    return data[["Open", "High", "Low", "Close"]]


def fetch_h1():
    data = fetch_candles(35)
    return data.resample("1h").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()


def fetch_m3():
    data = fetch_candles(5)
    return data.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()
