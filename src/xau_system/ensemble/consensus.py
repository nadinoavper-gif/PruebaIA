from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TimeframeVote:
    timeframe: str
    probs: list[float]  # [buy, sell, neutral]
    confidence: float
    weight: float


def _normalize(v: list[float]) -> list[float]:
    s = sum(max(0.0, x) for x in v)
    if s <= 0:
        return [0.0, 0.0, 1.0]
    return [max(0.0, x) / s for x in v]


def weighted_vote(votes: list[TimeframeVote]) -> list[float]:
    if not votes:
        return [0.0, 0.0, 1.0]
    num = [0.0, 0.0, 0.0]
    den = 0.0
    for v in votes:
        w = max(0.0, float(v.weight) * float(v.confidence))
        p = _normalize(v.probs)
        num = [num[i] + w * p[i] for i in range(3)]
        den += w
    if den <= 0:
        return [0.0, 0.0, 1.0]
    out = [x / den for x in num]
    return _normalize(out)


def apply_multitimeframe_gate(
    probs_1h: list[float],
    probs_4h: list[float],
    probs_d1: list[float],
    buy_th: float = 0.62,
    sell_th: float = 0.62,
) -> str:
    p_buy_1h, p_sell_1h, _ = probs_1h
    p_buy_4h, p_sell_4h, _ = probs_4h
    p_buy_d1, p_sell_d1, _ = probs_d1

    if p_buy_1h > buy_th and p_buy_4h > 0.60 and p_sell_d1 < 0.50:
        return "BUY"
    if p_sell_1h > sell_th and p_sell_4h > 0.60 and p_buy_d1 < 0.50:
        return "SELL"
    return "NEUTRAL"
