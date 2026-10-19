
import lzma
import struct
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://datafeed.dukascopy.com/datafeed"

session = requests.Session()

retry = Retry(
    total=2,
    connect=2,
    read=2,
    backoff_factor=5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
)

session.mount("https://", HTTPAdapter(max_retries=retry))


def fetch_day(day):
    url = (
        f"{BASE_URL}/XAUUSD/{day.year}/"
        f"{day.month - 1:02d}/{day.day:02d}/"
        "BID_candles_min_1.bi5"
    )

    for attempt in range(3):
        try:
            response = session.get(url, timeout=(15, 45))

            if response.status_code == 404:
                return []

            if response.status_code == 429:
                if attempt < 2:
                    wait = 30 * (attempt + 1)
                    print(f"Rate limited. Waiting {wait} seconds...")
                    time.sleep(wait)
                    continue

                raise RuntimeError(
                    "Dukascopy is rate-limiting this runner (HTTP 429). "
                    "Wait before trying again."
                )

            response.raise_for_status()

            if not response.content:
                return []

            raw = lzma.decompress(
                response.content,
                format=lzma.FORMAT_ALONE,
            )

            rows = []

            for offset in range(0, len(raw), 24):
                chunk = raw[offset:offset + 24]

                if len(chunk) != 24:
                    continue

                seconds, open_, close, low, high, volume = (
                    struct.unpack(">IIIIIf", chunk)
                )

                rows.append({
                    "Time": day + timedelta(seconds=seconds),
                    "Open": open_ / 1000,
                    "High": high / 1000,
                    "Low": low / 1000,
                    "Close": close / 1000,
                })

            return rows

        except requests.RequestException as exc:
            if attempt == 2:
                raise RuntimeError(
                    f"Download failed for {day.date()}: {exc}"
                ) from exc

            time.sleep(5 * (attempt + 1))

    return []


def fetch_candles(days):
    today = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    start = today - timedelta(days=days - 1)
    rows = []
    day = start
    total = days

    while day <= today:
        print(f"Downloading gold data: {(day - start).days + 1}/{total}")
        rows.extend(fetch_day(day))
        day += timedelta(days=1)
        time.sleep(3)

    if not rows:
        raise RuntimeError("No gold candles received from Dukascopy.")

    data = pd.DataFrame(rows)
    data["Time"] = pd.to_datetime(data["Time"], utc=True)
    data = data.set_index("Time").sort_index()
    data = data[~data.index.duplicated(keep="last")]

    return data[["Open", "High", "Low", "Close"]]


def fetch_h1():
    data = fetch_candles(3)

    result = data.resample("1h").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()

    if len(result) < 2:
        raise RuntimeError("Not enough H1 gold candles received.")

    return result


def fetch_m3():
    data = fetch_candles(2)

    result = data.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()

    if len(result) < 3:
        raise RuntimeError("Not enough M3 gold candles received.")

    return result
