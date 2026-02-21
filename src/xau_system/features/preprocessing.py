from __future__ import annotations

import numpy as np
import pandas as pd


def rolling_zscore(series: pd.Series, window: int = 100) -> pd.Series:
    mean = series.rolling(window).mean()
    std = series.rolling(window).std().replace(0, np.nan)
    return (series - mean) / std


def add_returns_and_atr(df: pd.DataFrame, atr_window: int = 14) -> pd.DataFrame:
    out = df.copy()
    out["log_return"] = np.log(out["close"] / out["close"].shift(1))
    prev_close = out["close"].shift(1)
    tr = pd.concat(
        [
            (out["high"] - out["low"]).abs(),
            (out["high"] - prev_close).abs(),
            (out["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr"] = tr.rolling(atr_window).mean()
    out["close_z"] = rolling_zscore(out["close"])
    out["volume_rel"] = out["volume"] / out["volume"].rolling(30).median()
    return out.dropna().reset_index(drop=True)


def normalize_ohlc_by_atr(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    eps = 1e-8
    for c in ["open", "high", "low", "close"]:
        out[f"{c}_norm"] = (out[c] - out["close"].shift(1)) / (out["atr"] + eps)
    return out.dropna().reset_index(drop=True)
