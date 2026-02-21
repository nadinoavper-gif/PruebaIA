from __future__ import annotations


def trade_reward(
    net_return: float,
    dd_increment: float,
    turnover_cost: float,
    regime_mismatch: float,
    a: float = 1.0,
    b: float = 0.5,
    c: float = 0.2,
    d: float = 0.2,
) -> float:
    return a * net_return - b * dd_increment - c * turnover_cost - d * regime_mismatch
