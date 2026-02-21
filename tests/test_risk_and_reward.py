from xau_system.risk.position_sizing import compute_sl_tp, risk_fraction
from xau_system.rl.reward import trade_reward


def test_risk_fraction_limits():
    assert risk_fraction(0.95, "trend", 0.9) == 0.03
    assert risk_fraction(0.80, "stable", 0.8) == 0.02
    assert risk_fraction(0.50, "range", 0.4) == 0.01


def test_compute_sl_tp_buy_sell():
    sl_buy, tp_buy = compute_sl_tp(2300, 10, "BUY")
    assert sl_buy < 2300 < tp_buy

    sl_sell, tp_sell = compute_sl_tp(2300, 10, "SELL")
    assert tp_sell < 2300 < sl_sell


def test_trade_reward_penalizes_costs():
    r1 = trade_reward(0.02, 0.0, 0.0, 0.0)
    r2 = trade_reward(0.02, 0.01, 0.01, 0.01)
    assert r1 > r2
