from __future__ import annotations

from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd


BINANCE_TIMEFRAME_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
}

YF_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "60m",
    "4h": "60m",
    "1d": "1d",
}


def _ensure_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    renamed = df.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    cols = ["open", "high", "low", "close", "volume"]
    out = renamed[cols].dropna().copy()
    out.index.name = "timestamp"
    return out


def fetch_binance_futures(symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
    import ccxt

    exchange = ccxt.binance({"enableRateLimit": True, "options": {"defaultType": "future"}})

    tf = BINANCE_TIMEFRAME_MAP.get(timeframe)
    if tf is None:
        raise ValueError(f"Unsupported timeframe for Binance: {timeframe}")

    since = int(pd.Timestamp(start_date, tz="UTC").timestamp() * 1000)
    end_ms = int(pd.Timestamp(end_date, tz="UTC").timestamp() * 1000)

    rows = []
    cursor = since
    while cursor < end_ms:
        batch = exchange.fetch_ohlcv(symbol=symbol, timeframe=tf, since=cursor, limit=1500)
        if not batch:
            break
        rows.extend(batch)
        last_ts = batch[-1][0]
        next_cursor = last_ts + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        if last_ts >= end_ms:
            break

    if not rows:
        raise ValueError("No Binance data returned")

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("timestamp")
    df = df[(df.index >= pd.Timestamp(start_date, tz="UTC")) & (df.index <= pd.Timestamp(end_date, tz="UTC"))]
    return df[["open", "high", "low", "close", "volume"]].dropna()


def fetch_yfinance(symbol: str, timeframe: str, start_date: str, end_date: str) -> pd.DataFrame:
    import yfinance as yf

    interval = YF_INTERVAL_MAP.get(timeframe)
    if interval is None:
        raise ValueError(f"Unsupported timeframe for yfinance: {timeframe}")

    yf_symbol = symbol.replace("USDT", "-USD")
    df = yf.download(yf_symbol, start=start_date, end=end_date, interval=interval, auto_adjust=False, progress=False)
    if df.empty:
        raise ValueError("No yfinance data returned")
    return _ensure_ohlcv(df)


def fetch_synthetic(start_date: str, end_date: str, timeframe: str = "15m") -> pd.DataFrame:
    freq = {"15m": "15min", "1h": "1H", "1d": "1D"}.get(timeframe, "15min")
    index = pd.date_range(start=start_date, end=end_date, freq=freq, tz="UTC")
    if len(index) < 10:
        raise ValueError("Synthetic date range too short")

    seed = 42
    rng = np.random.default_rng(seed)
    base = 100.0 + np.cumsum(rng.normal(loc=0.02, scale=0.8, size=len(index)))

    close = pd.Series(base, index=index)
    open_ = close.shift(1).fillna(close.iloc[0])
    spread = pd.Series(rng.uniform(0.2, 1.2, size=len(index)), index=index)

    high = pd.concat([open_, close], axis=1).max(axis=1) + spread
    low = pd.concat([open_, close], axis=1).min(axis=1) - spread
    volume = pd.Series(rng.uniform(100, 1000, size=len(index)), index=index)

    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close, "volume": volume}, index=index)


def fetch_data(symbol: str, timeframe: str, start_date: str, end_date: str, source: str = "binance") -> pd.DataFrame:
    source = source.lower()
    if source == "binance":
        return fetch_binance_futures(symbol, timeframe, start_date, end_date)
    if source == "yfinance":
        return fetch_yfinance(symbol, timeframe, start_date, end_date)
    if source == "synthetic":
        return fetch_synthetic(start_date, end_date, timeframe)
    raise ValueError(f"Unsupported data source: {source}")
