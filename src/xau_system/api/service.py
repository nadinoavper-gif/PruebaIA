from __future__ import annotations

from xau_system.config import Settings
from xau_system.ensemble.consensus import TimeframeVote, apply_multitimeframe_gate, weighted_vote
from xau_system.features.fundamental import FundamentalSnapshot, compute_fundamental_bias
from xau_system.risk.position_sizing import compute_sl_tp, risk_fraction
from xau_system.utils.types import SignalOutput


class SignalEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    @staticmethod
    def _normalize(v: list[float]) -> list[float]:
        s = sum(max(1e-6, x) for x in v)
        return [max(1e-6, x) / s for x in v]

    @staticmethod
    def _apply_bias_and_volume_confirmation(
        probs: list[float],
        signal: str,
        fundamental_bias: float,
        chaikin_ok: bool,
    ) -> list[float]:
        adj = probs.copy()

        if fundamental_bias > 0:
            adj[0] += 0.08 * fundamental_bias
            adj[1] -= 0.05 * fundamental_bias
        elif fundamental_bias < 0:
            f = abs(fundamental_bias)
            adj[1] += 0.08 * f
            adj[0] -= 0.05 * f

        if signal in {"BUY", "SELL"} and not chaikin_ok:
            adj[2] += 0.12
            if signal == "BUY":
                adj[0] -= 0.08
            else:
                adj[1] -= 0.08

        return SignalEngine._normalize(adj)

    def infer_from_probabilities(
        self,
        price: float,
        atr: float,
        votes: list[TimeframeVote],
        d1_probs: list[float],
        pattern_quality: float,
        regime: str,
        fundamentals: FundamentalSnapshot | None = None,
        chaikin_ok: bool = True,
    ) -> SignalOutput:
        agg = weighted_vote(votes)
        probs_1h = next((v.probs for v in votes if v.timeframe == "1H"), agg)
        probs_4h = next((v.probs for v in votes if v.timeframe == "4H"), agg)
        signal = apply_multitimeframe_gate(
            probs_1h=probs_1h,
            probs_4h=probs_4h,
            probs_d1=d1_probs,
            buy_th=self.settings.buy_threshold,
            sell_th=self.settings.sell_threshold,
        )

        f_bias = compute_fundamental_bias(fundamentals or FundamentalSnapshot())
        agg = self._apply_bias_and_volume_confirmation(agg, signal, f_bias, chaikin_ok)

        confidence = max(agg)
        risk = risk_fraction(confidence, regime, pattern_quality)
        sl, tp = compute_sl_tp(price, atr, signal)

        pad = 0.15 * max(atr, 1e-6)
        return SignalOutput(
            instrument=self.settings.instrument,
            signal=signal,
            confidence=float(confidence),
            entry_zone=(price - pad, price + pad),
            stop_zone=(sl - pad, sl + pad),
            targets=(tp, tp + (0.8 * atr if signal == "BUY" else -0.8 * atr)),
            risk_fraction=risk,
        )
