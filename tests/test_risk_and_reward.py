from xau_system.risk.position_sizing import compute_sl_tp, profit_target_pct, risk_fraction
from xau_system.rl.reward import trade_reward


def test_risk_fraction_is_always_1pct():
    assert risk_fraction(0.95, "trend", 0.9) == 0.01
    assert risk_fraction(0.80, "stable", 0.8) == 0.01
    assert risk_fraction(0.50, "range", 0.4) == 0.01


def test_profit_target_pct_bounds():
    assert profit_target_pct(0.79) == 0.02
    assert profit_target_pct(0.80) == 0.03
    assert profit_target_pct(0.99) == 0.03


def test_compute_sl_tp_buy_sell_with_pct_target():
    sl_buy, tp_buy = compute_sl_tp(2300, 10, "BUY", tp_pct=0.02)
    assert sl_buy < 2300 < tp_buy
    assert round(tp_buy, 2) == 2346.00

    sl_sell, tp_sell = compute_sl_tp(2300, 10, "SELL", tp_pct=0.03)
    assert tp_sell < 2300 < sl_sell
    assert round(tp_sell, 2) == 2231.00


def test_trade_reward_penalizes_costs():
    r1 = trade_reward(0.02, 0.0, 0.0, 0.0)
    r2 = trade_reward(0.02, 0.01, 0.01, 0.01)
    assert r1 > r2
