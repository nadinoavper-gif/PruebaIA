from dataclasses import dataclass
from typing import Literal


SignalType = Literal["BUY", "SELL", "NEUTRAL"]


@dataclass
class SignalOutput:
    instrument: str
    signal: SignalType
    confidence: float
    entry_zone: tuple[float, float]
    stop_zone: tuple[float, float]
    targets: tuple[float, float]
    risk_fraction: float
