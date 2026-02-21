from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OnlineUpdateResult:
    promoted: bool
    reason: str


def gating_decision(
    sharpe_old: float,
    sharpe_new: float,
    mdd_old: float,
    mdd_new: float,
    max_mdd_deterioration: float = 0.02,
) -> OnlineUpdateResult:
    if sharpe_new < sharpe_old:
        return OnlineUpdateResult(False, "Sharpe degradado")
    if (mdd_new - mdd_old) > max_mdd_deterioration:
        return OnlineUpdateResult(False, "Max drawdown degradado")
    return OnlineUpdateResult(True, "Modelo challenger promovido")
