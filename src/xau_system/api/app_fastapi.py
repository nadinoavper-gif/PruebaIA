from __future__ import annotations

from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from xau_system.api.service import SignalEngine
from xau_system.data.live_price import BufferPriceProvider, CompositePriceProvider, FixedPriceProvider, MT5PriceProvider
from xau_system.data.realtime import MarketBar, RealTimeBuffer
from xau_system.ensemble.consensus import TimeframeVote
from xau_system.features.fundamental import FundamentalSnapshot
from xau_system.integrations.mt5_bridge import MT5Bridge, MT5OrderRequest
from xau_system.integrations.tradingview_feed import TradingViewFeed, build_analysis_from_payload
from xau_system.rl.online_trainer import OnlineTrainer
from xau_system.ui.dashboard import dashboard_response

app = FastAPI(title="XAU/USD AI Signal Service", version="0.4.0")
engine = SignalEngine()
realtime_buffer = RealTimeBuffer()
mt5_bridge = MT5Bridge()
price_provider = CompositePriceProvider(
    providers=[
        MT5PriceProvider(mt5_bridge),
        BufferPriceProvider(realtime_buffer),
        FixedPriceProvider(2300.0, source="fixed-fallback"),
    ]
)
tv_feed = TradingViewFeed()
online_trainer = OnlineTrainer()


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
    price: float | None = None
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


class MT5OrderInput(BaseModel):
    side: str = Field(pattern="^(BUY|SELL)$")
    lot: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    symbol: str = "XAUUSD"
    deviation: int = 20
    comment: str = "xau_system"


class TradingViewPayload(BaseModel):
    timestamp: str | None = None
    symbol: str = "XAUUSD"
    timeframe: str = "1H"
    source: str = "tradingview"
    note: str = "alerta tradingview"
    pattern: str | None = None
    rsi: float | None = None
    macd: float | None = None
    chaikin_ad: float | None = None
    fundamental_bias: float | None = None
    chart_image_url: str | None = None




@app.get("/")
def ui_root():
    return dashboard_response()


@app.get("/ui")
def ui_dashboard():
    return dashboard_response()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "instrument": "XAUUSD"}


@app.get("/market/xauusd/price")
def get_market_price() -> dict:
    tick = price_provider.get_tick("XAUUSD")
    if tick is None:
        raise HTTPException(status_code=503, detail="No hay precio disponible")
    return {
        "symbol": tick.symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "last": tick.last,
        "timestamp": tick.timestamp.isoformat(),
        "source": tick.source,
    }


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


@app.post("/mt5/initialize")
def mt5_initialize() -> dict:
    ok, msg = mt5_bridge.initialize()
    return {"ok": ok, "message": msg}


@app.post("/mt5/order")
def mt5_order(payload: MT5OrderInput) -> dict:
    req = MT5OrderRequest(
        symbol=payload.symbol,
        side=payload.side,
        lot=payload.lot,
        stop_loss=payload.stop_loss,
        take_profit=payload.take_profit,
        deviation=payload.deviation,
        comment=payload.comment,
    )
    ok, msg, request = mt5_bridge.send_market_order(req)
    return {"ok": ok, "message": msg, "request": request}


@app.post("/training/start")
def training_start() -> dict:
    started = online_trainer.start()
    return {"started": started, "running": online_trainer.status().running}


@app.post("/training/stop")
def training_stop() -> dict:
    stopped = online_trainer.stop()
    return {"stopped": stopped, "running": online_trainer.status().running}


@app.get("/training/status")
def training_status() -> dict:
    st = online_trainer.status()
    return {
        "running": st.running,
        "steps": st.steps,
        "last_loss": st.last_loss,
        "last_update_ts": st.last_update_ts,
    }


@app.post("/tradingview/analysis")
def tradingview_analysis(payload: TradingViewPayload) -> dict:
    analysis = build_analysis_from_payload(payload.model_dump())
    tv_feed.append(analysis)
    return {"ok": True, "symbol": analysis.symbol, "timeframe": analysis.timeframe}


@app.get("/tradingview/analysis/latest")
def tradingview_latest(n: int = 20) -> list[dict]:
    return tv_feed.latest(n)


@app.post("/signal/xauusd")
def get_signal(payload: SignalRequest) -> dict:
    votes = [TimeframeVote(v.timeframe, list(v.probs), v.confidence, v.weight) for v in payload.votes]
    fundamentals = (
        FundamentalSnapshot(**payload.fundamentals.model_dump())
        if payload.fundamentals is not None
        else FundamentalSnapshot()
    )

    live_tick = price_provider.get_tick("XAUUSD")
    market_price = payload.price if payload.price is not None else (live_tick.last if live_tick else None)
    if market_price is None:
        raise HTTPException(status_code=503, detail="No se pudo determinar precio automático de XAUUSD")

    out = engine.infer_from_probabilities(
        price=market_price,
        atr=payload.atr,
        votes=votes,
        d1_probs=list(payload.d1_probs),
        pattern_quality=payload.pattern_quality,
        regime=payload.regime,
        fundamentals=fundamentals,
        chaikin_ok=payload.chaikin_ok,
    )
    result = out.__dict__
    result["price_source"] = live_tick.source if payload.price is None and live_tick else "manual"
    return result
