from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FundamentalSnapshot:
    usd_index: float | None = None
    real_yield_10y: float | None = None
    fed_rate: float | None = None
    risk_aversion_score: float | None = None


def compute_fundamental_bias(s: FundamentalSnapshot) -> float:
    """Score [-1,1]: positivo favorece sesgo alcista para oro."""
    score = 0.0
    weight = 0.0

    if s.usd_index is not None:
        # USD fuerte suele presionar oro a la baja
        score += -0.35 * ((s.usd_index - 100.0) / 10.0)
        weight += 0.35

    if s.real_yield_10y is not None:
        # Real yields altas tienden a ser bajistas para oro
        score += -0.35 * (s.real_yield_10y / 2.0)
        weight += 0.35

    if s.fed_rate is not None:
        # Tasas altas suelen restar atractivo al oro
        score += -0.15 * (s.fed_rate / 5.0)
        weight += 0.15

    if s.risk_aversion_score is not None:
        # Mayor aversión al riesgo puede beneficiar oro refugio
        score += 0.15 * s.risk_aversion_score
        weight += 0.15

    if weight == 0:
        return 0.0

    norm = score / weight
    return max(-1.0, min(1.0, norm))
