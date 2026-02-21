from dataclasses import dataclass


@dataclass
class Settings:
    instrument: str = "XAUUSD"
    lookback_bars: int = 128
    risk_base: float = 0.01
    risk_high: float = 0.02
    risk_max: float = 0.03
    buy_threshold: float = 0.62
    sell_threshold: float = 0.62
    neutral_threshold: float = 0.50
