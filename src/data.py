import requests
import pandas as pd

API_URL = "https://xaus.com/api/v1/chart"


def fetch_candles(interval, period):
    response = requests.get(
        API_URL,
        params={
            "symbol": "xau",
            "range": period,
            "interval": interval,
        },
        timeout=30,
    )
    response.raise_for_status()

    payload = response.json()
    points = payload.get("points", [])

    if not points:
        raise RuntimeError(
            "Gold API returned no candles: "
            + str(payload)[:300]
        )

    data = pd.DataFrame(points)
    required = ["t", "o", "h", "l", "c"]

    if not all(column in data.columns for column in required):
        raise RuntimeError(
            "Unexpected API response: "
            + str(list(data.columns))
        )

    data = data.rename(columns={
        "t": "Time",
        "o": "Open",
        "h": "High",
        "l": "Low",
        "c": "Close",
        "v": "Volume",
    })

    data["Time"] = pd.to_datetime(
        data["Time"], unit="s", utc=True
    )

    data = data.set_index("Time")
    data = data[["Open", "High", "Low", "Close"]]
    data = data.apply(pd.to_numeric, errors="coerce")
    data = data.dropna().sort_index()

    if data.empty:
        raise RuntimeError("Gold candle data is empty")

    return data


def fetch_h1():
    return fetch_candles("1h", "1mo")


def fetch_m3():
    data = fetch_candles("1m", "5d")

    candles = data.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()

    return candles
