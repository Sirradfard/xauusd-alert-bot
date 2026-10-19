import yfinance as yf
import pandas as pd


SYMBOL = "XAUUSD=X"


def fetch_h1():
    data = yf.download(
        SYMBOL,
        period="10d",
        interval="1h",
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise RuntimeError("No H1 data received for " + SYMBOL)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close"]].dropna()
    data.index = pd.to_datetime(data.index, utc=True)

    return data.sort_index()


def fetch_m3():
    data = yf.download(
        SYMBOL,
        period="5d",
        interval="1m",
        auto_adjust=False,
        progress=False,
    )

    if data.empty:
        raise RuntimeError("No M1 data received for " + SYMBOL)

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data[["Open", "High", "Low", "Close", "Volume"]].dropna()
    data.index = pd.to_datetime(data.index, utc=True)

    candles = data.resample("3min").agg({
        "Open": "first",
        "High": "max",
        "Low": "min",
        "Close": "last",
        "Volume": "sum",
    }).dropna(subset=["Open", "High", "Low", "Close"])

    return candles.sort_index()
