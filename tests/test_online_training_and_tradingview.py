import json
import time

from xau_system.integrations.tradingview_feed import TradingViewFeed, build_analysis_from_payload
from xau_system.rl.experience_buffer import Experience, ExperienceBuffer
from xau_system.rl.online_trainer import OnlineTrainer


def test_tradingview_feed_append_and_latest(tmp_path):
    path = tmp_path / "tv.ndjson"
    feed = TradingViewFeed(str(path))
    payload = {
        "symbol": "XAUUSD",
        "timeframe": "1H",
        "pattern": "triangle",
        "rsi": 58.2,
        "fundamental_bias": 0.3,
        "chart_image_url": "https://example.com/chart.png",
    }
    analysis = build_analysis_from_payload(payload)
    feed.append(analysis)
    latest = feed.latest(5)
    assert len(latest) == 1
    assert latest[0]["symbol"] == "XAUUSD"
    assert latest[0]["pattern"] == "triangle"


def test_online_trainer_processes_new_experiences(tmp_path):
    exp_path = tmp_path / "experiences.ndjson"
    exp_buf = ExperienceBuffer(str(exp_path))
    trainer = OnlineTrainer(experience_path=str(exp_path), poll_s=0.05)

    started = trainer.start()
    assert started is True

    exp_buf.append(Experience("s1", "BUY", 0.8, 0.01, 12.3, "trend"))
    exp_buf.append(Experience("s2", "SELL", 0.6, -0.005, -3.2, "range"))

    time.sleep(0.2)
    st = trainer.status()
    assert st.running is True
    assert st.steps >= 2

    stopped = trainer.stop()
    assert stopped is True
