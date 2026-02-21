from __future__ import annotations


def risk_fraction(confidence: float, regime: str, pattern_quality: float) -> float:
    """Política solicitada: riesgo fijo del 1% por operación."""
    _ = (confidence, regime, pattern_quality)
    return 0.01


def profit_target_pct(confidence: float) -> float:
    """Objetivo de beneficio: 2% por defecto, 3% máximo en alta confianza."""
    return 0.03 if confidence >= 0.80 else 0.02


def compute_sl_tp(
    entry: float,
    atr: float,
    direction: str,
    rr: float = 2.0,
    tp_pct: float | None = None,
) -> tuple[float, float]:
    """
    SL técnico por ATR y TP por porcentaje si se especifica.
    - riesgo de cuenta se controla en risk_fraction (1%).
    - beneficio objetivo 2%-3% mediante tp_pct.
    """
    atr = max(atr, 1e-6)
    if direction == "BUY":
        sl = entry - 1.2 * atr
        tp = entry * (1.0 + tp_pct) if tp_pct is not None else entry + (entry - sl) * rr
    elif direction == "SELL":
        sl = entry + 1.2 * atr
        tp = entry * (1.0 - tp_pct) if tp_pct is not None else entry - (sl - entry) * rr
    else:
        sl = entry
        tp = entry
    return sl, tp
