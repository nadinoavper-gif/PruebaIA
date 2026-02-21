from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass
class MarketFrame:
    timeframe: str
    data: pd.DataFrame


def load_ohlcv_csv(path: str, timeframe: str) -> MarketFrame:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp").drop_duplicates("timestamp")
    return MarketFrame(timeframe=timeframe, data=df.reset_index(drop=True))


def resample_frame(frame: MarketFrame, timeframe: str) -> MarketFrame:
    df = frame.data.set_index("timestamp")
    rs = df.resample(timeframe).agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    ).dropna()
    return MarketFrame(timeframe=timeframe, data=rs.reset_index())
