import numpy as np
import pandas as pd

from quark.backtest.metrics import (
    deflated_sharpe,
    expected_max_sharpe,
    max_drawdown,
    probabilistic_sharpe,
    summary_stats,
)


def test_max_drawdown_hand_computed():
    eq = pd.Series([1.0, 1.2, 0.9, 1.1])
    assert np.isclose(max_drawdown(eq), 0.9 / 1.2 - 1.0)  # -25%


def test_max_drawdown_monotonic_equity_is_zero():
    eq = pd.Series([1.0, 1.1, 1.2, 1.3])
    assert max_drawdown(eq) == 0.0


def test_cagr_geometric():
    daily = 1.10 ** (1 / 252) - 1  # exactly +10%/yr compounded
    r = pd.Series(daily, index=pd.bdate_range("2020-01-01", periods=504))
    r.iloc[::2] += 1e-4  # break constant-series degeneracy
    r.iloc[1::2] -= 1e-4
    stats = summary_stats(r)
    assert np.isclose(stats["cagr"], 0.10, atol=5e-3)


def test_sharpe_of_alternating_series():
    vals = np.tile([0.011, -0.009], 500)
    r = pd.Series(vals, index=pd.bdate_range("2015-01-01", periods=1000))
    stats = summary_stats(r)
    expected = vals.mean() / vals.std(ddof=1) * np.sqrt(252)
    assert np.isclose(stats["sharpe"], expected, rtol=1e-6)
    assert stats["hit_rate"] == 0.5


def test_psr_large_t_positive_sr_near_one():
    assert probabilistic_sharpe(0.1, 5000, 0.0, 3.0) > 0.99


def test_expected_max_sharpe_properties():
    assert expected_max_sharpe(1, 0.01) == 0.0
    e10 = expected_max_sharpe(10, 0.01)
    e100 = expected_max_sharpe(100, 0.01)
    assert 0 < e10 < e100  # more trials -> higher bar


def test_dsr_shrinks_with_trials():
    rng = np.random.default_rng(42)
    r = pd.Series(rng.normal(0.0004, 0.01, 2500),
                  index=pd.bdate_range("2015-01-01", periods=2500))
    sr_var = 0.25 / 252  # plausible dispersion of trial SRs (daily units)
    d1 = deflated_sharpe(r, n_trials=1, sr_var=sr_var)
    d100 = deflated_sharpe(r, n_trials=100, sr_var=sr_var)
    assert d1["sr_star_daily"] == 0.0
    assert d100["sr_star_daily"] > 0.0
    assert d100["dsr"] < d1["dsr"]
    assert 0.0 <= d100["dsr"] <= 1.0
