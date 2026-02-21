from __future__ import annotations

from dataclasses import dataclass
import json
from urllib import request

from xau_system.api.service import SignalEngine
from xau_system.ensemble.consensus import TimeframeVote
from xau_system.features.fundamental import FundamentalSnapshot


@dataclass
class SmokeResult:
    ok: bool
    detail: str


class ImplementationModule:
    """Módulo de implementación: guía programática para usar y probar el sistema."""

    @staticmethod
    def default_signal_payload() -> dict:
        return {
            "atr": 12.0,
            "pattern_quality": 0.8,
            "regime": "trend",
            "d1_probs": [0.55, 0.20, 0.25],
            "votes": [
                {"timeframe": "1H", "probs": [0.70, 0.15, 0.15], "confidence": 0.8, "weight": 1.0},
                {"timeframe": "4H", "probs": [0.66, 0.18, 0.16], "confidence": 0.8, "weight": 1.0},
            ],
            "chaikin_ok": True,
            "fundamentals": {
                "usd_index": 100.0,
                "real_yield_10y": 1.0,
                "fed_rate": 4.5,
                "risk_aversion_score": 0.2,
            },
        }

    @staticmethod
    def smoke_test_core(price: float = 2300.0) -> SmokeResult:
        try:
            payload = ImplementationModule.default_signal_payload()
            votes = [
                TimeframeVote(v["timeframe"], v["probs"], v["confidence"], v["weight"])
                for v in payload["votes"]
            ]
            fundamentals = FundamentalSnapshot(**payload["fundamentals"])

            engine = SignalEngine()
            out = engine.infer_from_probabilities(
                price=price,
                atr=float(payload["atr"]),
                votes=votes,
                d1_probs=payload["d1_probs"],
                pattern_quality=float(payload["pattern_quality"]),
                regime=str(payload["regime"]),
                fundamentals=fundamentals,
                chaikin_ok=bool(payload["chaikin_ok"]),
            )
            if out.instrument != "XAUUSD":
                return SmokeResult(False, "Instrumento incorrecto")
            if out.risk_fraction != 0.01:
                return SmokeResult(False, "Política de riesgo incorrecta")
            return SmokeResult(True, f"Señal={out.signal} conf={out.confidence:.3f}")
        except Exception as e:
            return SmokeResult(False, f"Error core smoke test: {e}")

    @staticmethod
    def smoke_test_api(base_url: str = "http://127.0.0.1:8000") -> SmokeResult:
        payload = ImplementationModule.default_signal_payload()
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            url=f"{base_url}/signal/xauusd",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "signal" not in data:
                return SmokeResult(False, "API sin campo signal")
            return SmokeResult(True, f"API ok signal={data['signal']}")
        except Exception as e:
            return SmokeResult(False, f"API smoke test falló: {e}")
