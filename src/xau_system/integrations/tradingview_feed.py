from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from pathlib import Path


@dataclass
class TradingViewAnalysis:
    timestamp: str
    symbol: str
    timeframe: str
    source: str
    note: str
    pattern: str | None = None
    rsi: float | None = None
    macd: float | None = None
    chaikin_ad: float | None = None
    fundamental_bias: float | None = None
    chart_image_url: str | None = None


class TradingViewFeed:
    """Persistencia local de análisis enviados por alertas/webhooks de TradingView."""

    def __init__(self, path: str = "data/tradingview_analysis.ndjson"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, analysis: TradingViewAnalysis) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(analysis)) + "\n")

    def latest(self, n: int = 20) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as f:
            lines = [ln for ln in f.readlines() if ln.strip()]
        out = []
        for line in lines[-n:]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


def build_analysis_from_payload(payload: dict) -> TradingViewAnalysis:
    now = datetime.now(timezone.utc).isoformat()
    return TradingViewAnalysis(
        timestamp=str(payload.get("timestamp", now)),
        symbol=str(payload.get("symbol", "XAUUSD")),
        timeframe=str(payload.get("timeframe", "1H")),
        source=str(payload.get("source", "tradingview")),
        note=str(payload.get("note", "alerta recibida")),
        pattern=payload.get("pattern"),
        rsi=payload.get("rsi"),
        macd=payload.get("macd"),
        chaikin_ad=payload.get("chaikin_ad"),
        fundamental_bias=payload.get("fundamental_bias"),
        chart_image_url=payload.get("chart_image_url"),
    )
