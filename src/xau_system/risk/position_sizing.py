from __future__ import annotations


def risk_fraction(confidence: float, regime: str, pattern_quality: float) -> float:
    risk = 0.01
    if confidence > 0.75 and pattern_quality > 0.70 and regime in {"trend", "stable"}:
        risk = 0.02
    if confidence > 0.88 and pattern_quality > 0.85 and regime == "trend":
        risk = 0.03
    return min(max(risk, 0.0), 0.03)


def compute_sl_tp(entry: float, atr: float, direction: str, rr: float = 2.0) -> tuple[float, float]:
    atr = max(atr, 1e-6)
    if direction == "BUY":
        sl = entry - 1.2 * atr
        tp = entry + (entry - sl) * rr
    elif direction == "SELL":
        sl = entry + 1.2 * atr
        tp = entry - (sl - entry) * rr
    else:
        sl = entry
        tp = entry
    return sl, tp
