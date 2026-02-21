from datetime import datetime, timezone

from xau_system.data.live_price import BufferPriceProvider, CompositePriceProvider, FixedPriceProvider
from xau_system.data.realtime import MarketBar, RealTimeBuffer
from xau_system.integrations.mt5_bridge import MT5Bridge, MT5OrderRequest


def test_composite_provider_prefers_buffer_when_data_exists(tmp_path):
    buf = RealTimeBuffer(maxlen=10, persist_path=str(tmp_path / "rt.ndjson"))
    buf.append(
        MarketBar(
            timestamp=datetime.now(timezone.utc),
            open=2299,
            high=2302,
            low=2298,
            close=2301,
            volume=1000,
            source="test",
        )
    )

    provider = CompositePriceProvider([BufferPriceProvider(buf), FixedPriceProvider(2200.0)])
    tick = provider.get_tick("XAUUSD")
    assert tick is not None
    assert tick.last == 2301
    assert tick.source.startswith("buffer")


def test_composite_provider_fallback_to_fixed(tmp_path):
    buf = RealTimeBuffer(maxlen=10, persist_path=str(tmp_path / "rt.ndjson"))
    provider = CompositePriceProvider([BufferPriceProvider(buf), FixedPriceProvider(2200.0, source="fallback")])
    tick = provider.get_tick("XAUUSD")
    assert tick is not None
    assert tick.last == 2200.0
    assert tick.source == "fallback"


def test_mt5_bridge_handles_unavailable_environment():
    bridge = MT5Bridge()
    # En este entorno normalmente no hay terminal MT5, debe fallar de forma controlada.
    if not bridge.available:
        ok, msg = bridge.initialize()
        assert ok is False
        assert "no disponible" in msg.lower()

        ok2, msg2, req = bridge.send_market_order(
            MT5OrderRequest(symbol="XAUUSD", side="BUY", lot=0.01, stop_loss=2200, take_profit=2350)
        )
        assert ok2 is False
        assert req == {}
