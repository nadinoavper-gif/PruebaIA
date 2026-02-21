from datetime import datetime, timezone


from xau_system.data.realtime import MarketBar, RealTimeBuffer
from xau_system.features.fundamental import FundamentalSnapshot, compute_fundamental_bias
from xau_system.api.service import SignalEngine
from xau_system.ensemble.consensus import TimeframeVote


def test_realtime_buffer_append_and_latest(tmp_path):
    p = tmp_path / "rt.ndjson"
    buf = RealTimeBuffer(maxlen=3, persist_path=str(p))
    for i in range(4):
        buf.append(
            MarketBar(
                timestamp=datetime.now(timezone.utc),
                open=1 + i,
                high=2 + i,
                low=0.5 + i,
                close=1.5 + i,
                volume=100 + i,
            )
        )
    assert len(buf) == 3
    assert len(buf.latest(2)) == 2
    assert p.exists()


def test_fundamental_bias_direction():
    bullish_gold = FundamentalSnapshot(usd_index=95, real_yield_10y=-0.5, fed_rate=1.0, risk_aversion_score=0.6)
    bearish_gold = FundamentalSnapshot(usd_index=110, real_yield_10y=2.0, fed_rate=5.0, risk_aversion_score=-0.4)
    assert compute_fundamental_bias(bullish_gold) > 0
    assert compute_fundamental_bias(bearish_gold) < 0


def test_signal_engine_uses_bias_and_confirmation():
    engine = SignalEngine()
    votes = [
        TimeframeVote("1H", [0.70, 0.15, 0.15], 0.8, 1.0),
        TimeframeVote("4H", [0.66, 0.18, 0.16], 0.8, 1.0),
    ]
    d1 = [0.55, 0.20, 0.25]
    out = engine.infer_from_probabilities(
        price=2300,
        atr=12,
        votes=votes,
        d1_probs=d1,
        pattern_quality=0.8,
        regime="trend",
        fundamentals=FundamentalSnapshot(usd_index=94, real_yield_10y=-0.6, fed_rate=1.0, risk_aversion_score=0.8),
        chaikin_ok=False,
    )
    assert out.signal in {"BUY", "SELL", "NEUTRAL"}
    assert 0.0 <= out.confidence <= 1.0
    assert out.risk_fraction == 0.01
