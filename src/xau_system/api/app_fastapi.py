from __future__ import annotations

from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel, Field

from xau_system.api.service import SignalEngine
from xau_system.data.realtime import MarketBar, RealTimeBuffer
from xau_system.ensemble.consensus import TimeframeVote
from xau_system.features.fundamental import FundamentalSnapshot

app = FastAPI(title="XAU/USD AI Signal Service", version="0.2.0")
engine = SignalEngine()
realtime_buffer = RealTimeBuffer()


class VoteInput(BaseModel):
    timeframe: str
    probs: list[float] = Field(description="[buy, sell, neutral]")
    confidence: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0)


class FundamentalInput(BaseModel):
    usd_index: float | None = None
    real_yield_10y: float | None = None
    fed_rate: float | None = None
    risk_aversion_score: float | None = Field(default=None, ge=-1.0, le=1.0)


class SignalRequest(BaseModel):
    price: float
    atr: float = Field(gt=0)
    pattern_quality: float = Field(ge=0.0, le=1.0)
    regime: str = "range"
    d1_probs: list[float]
    votes: list[VoteInput]
    chaikin_ok: bool = True
    fundamentals: FundamentalInput | None = None


class MarketBarInput(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "api"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "instrument": "XAUUSD"}


@app.post("/ingest/bar")
def ingest_bar(payload: MarketBarInput) -> dict[str, int]:
    ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    bar = MarketBar(
        timestamp=ts,
        open=payload.open,
        high=payload.high,
        low=payload.low,
        close=payload.close,
        volume=payload.volume,
        source=payload.source,
    )
    realtime_buffer.append(bar)
    return {"buffer_size": len(realtime_buffer)}


@app.get("/realtime/latest")
def latest_bars(n: int = 5) -> list[dict]:
    return [
        {
            "timestamp": b.timestamp.isoformat(),
            "open": b.open,
            "high": b.high,
            "low": b.low,
            "close": b.close,
            "volume": b.volume,
            "source": b.source,
        }
        for b in realtime_buffer.latest(n)
    ]


@app.post("/signal/xauusd")
def get_signal(payload: SignalRequest) -> dict:
    votes = [TimeframeVote(v.timeframe, list(v.probs), v.confidence, v.weight) for v in payload.votes]
    fundamentals = (
        FundamentalSnapshot(**payload.fundamentals.model_dump())
        if payload.fundamentals is not None
        else FundamentalSnapshot()
    )
    out = engine.infer_from_probabilities(
        price=payload.price,
        atr=payload.atr,
        votes=votes,
        d1_probs=list(payload.d1_probs),
        pattern_quality=payload.pattern_quality,
        regime=payload.regime,
        fundamentals=fundamentals,
        chaikin_ok=payload.chaikin_ok,
    )
    return out.__dict__
