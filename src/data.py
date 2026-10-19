
import yfinance as yf
import pandas as pd

SYMBOL = "GC=F"


def fetch_h1():
    data = yf.download(
        SYMBOL,
        period="10d",
        interval="1h",
        progress=False,
        auto_adjust=False,
    )

    if data.empty:
        raise RuntimeError("Yahoo Finance returned no H1 data")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    return data[["Open", "High", "Low", "Close"]].dropna()


def fetch_m3():
    data = yf.download(
        SYMBOL,
        period="5d",
        interval="1m",
        progress=False,
        auto_adjust=False,
    )

    if data.empty:
        raise RuntimeError("Yahoo Finance returned no 1-minute data")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close"]].dropna()

    candles = data.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
    }).dropna()

    return candles
