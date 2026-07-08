import numpy as np
import pandas as pd
import pytest

from conftest import make_universe
from quark.backtest.engine import run_backtest, run_weights_backtest


def jump_setup(dates, know_days_early: int):
    """Flat price that jumps +10% at day K and stays there. The signal turns
    on `know_days_early` days before the jump."""
    K = 200
    px = pd.Series(100.0, index=dates)
    px.iloc[K:] = 110.0
    sig = pd.Series(0.0, index=dates)
    sig.iloc[K - know_days_early :] = 1.0
    return px.to_frame("A"), sig.to_frame("A"), K


def test_no_lookahead(bdates):
    """THE test: a signal that only 'knows' about a price jump on the day it
    happens must earn exactly nothing from it."""
    prices, signals, K = jump_setup(bdates, know_days_early=0)
    res = run_backtest(signals, prices, universe=make_universe(["A"]), lag=1)
    assert res.gross_returns.iloc[K]["A"] == 0.0
    assert res.portfolio.sum() <= 0.0  # only costs remain


def test_one_day_foresight_captures_jump(bdates):
    prices, signals, K = jump_setup(bdates, know_days_early=1)
    res = run_backtest(signals, prices, universe=make_universe(["A"]), lag=1)
    assert res.gross_returns.iloc[K]["A"] > 0.0


def test_lag2_needs_two_days_foresight(bdates):
    prices, signals, K = jump_setup(bdates, know_days_early=1)
    res = run_backtest(signals, prices, universe=make_universe(["A"]), lag=2)
    assert res.gross_returns.iloc[K]["A"] == 0.0


def test_lag_zero_rejected(bdates):
    prices, signals, _ = jump_setup(bdates, 0)
    with pytest.raises(ValueError, match="lookahead"):
        run_backtest(signals, prices, universe=make_universe(["A"]), lag=0)


def test_perfect_foresight_is_profitable(bdates):
    rng = np.random.default_rng(7)
    rets = rng.normal(0, 0.01, len(bdates))
    prices = pd.DataFrame({"A": 100 * np.cumprod(1 + rets)}, index=bdates)
    r = prices["A"].pct_change()
    signals = np.sign(r.shift(-1)).to_frame("A")  # knows tomorrow's return
    res = run_backtest(signals, prices, universe=make_universe(["A"], cost_bps=0.0))
    assert res.gross_returns.sum().sum() > 0


def test_nan_prices_produce_finite_portfolio(bdates):
    rng = np.random.default_rng(11)
    prices = pd.DataFrame(
        {c: 100 * np.cumprod(1 + rng.normal(0, 0.01, len(bdates))) for c in "AB"},
        index=bdates,
    )
    prices.iloc[100:120, prices.columns.get_loc("B")] = np.nan
    signals = pd.DataFrame(1.0, index=bdates, columns=["A", "B"])
    res = run_backtest(signals, prices, universe=make_universe(["A", "B"]))
    assert res.portfolio.notna().all()
    assert np.isfinite(res.equity).all()


def test_nontradable_instruments_excluded(bdates):
    prices = pd.DataFrame({"A": 100.0, "TNX": 45.0}, index=bdates)
    signals = pd.DataFrame(1.0, index=bdates, columns=["A", "TNX"])
    uni = make_universe(["A", "TNX"])
    uni.loc["TNX", "tradable"] = False
    res = run_backtest(signals, prices, universe=uni)
    assert list(res.positions.columns) == ["A"]


def test_weights_backtest_hand_computed(bdates):
    dates = bdates[:5]
    returns = pd.DataFrame(
        {
            "A": [np.nan, 0.01, 0.02, -0.01, 0.03],
            "B": [np.nan, -0.02, 0.01, 0.00, -0.01],
        },
        index=dates,
    )
    weights = pd.DataFrame({"A": 0.5, "B": -0.5}, index=dates)
    res = run_weights_backtest(weights, returns, cost_bps=10.0, lag=1)
    # Day 1: enter 0.5/-0.5 (cost = 1.0 * 10bps), earn 0.5*0.01 - 0.5*(-0.02)
    expected_day1 = 0.015 - 1.0 * 10e-4
    assert np.isclose(res.portfolio.iloc[1], expected_day1)
    assert res.portfolio.iloc[0] == 0.0
    assert np.isclose(res.turnover.iloc[1], 1.0)


def test_cost_drag_in_portfolio_units(bdates):
    """Audit-pinned: cost_drag_ann must equal the actual gross-net gap of
    the PORTFOLIO return stream (not the per-instrument sum, ~N x larger)."""
    rng = np.random.default_rng(5)
    prices = pd.DataFrame(
        {c: 100 * np.cumprod(1 + rng.normal(0, 0.01, len(bdates)))
         for c in "ABCDE"}, index=bdates)
    signals = np.sign(prices.pct_change())
    res = run_backtest(signals, prices, universe=make_universe(list("ABCDE"),
                                                               cost_bps=20.0))
    n_years = len(res.portfolio) / 252
    gross_port = (res.gross_returns.fillna(0).sum(axis=1)
                  / prices.notna().cummax().sum(axis=1))
    actual_drag = float((gross_port - res.portfolio).sum() / n_years)
    assert np.isclose(res.stats["cost_drag_ann"], actual_drag, rtol=1e-6)


def test_gross_geq_net_with_costs(bdates):
    rng = np.random.default_rng(3)
    prices = pd.DataFrame({"A": 100 * np.cumprod(1 + rng.normal(0, 0.01, len(bdates)))},
                          index=bdates)
    signals = np.sign(prices["A"].pct_change()).to_frame("A")
    res = run_backtest(signals, prices, universe=make_universe(["A"], cost_bps=20.0))
    assert res.gross_returns.fillna(0).sum().sum() > res.net_returns.sum().sum()
