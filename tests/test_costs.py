import numpy as np
import pandas as pd

from quark.backtest.costs import turnover_costs


def make_positions(vals, ticker="A"):
    idx = pd.bdate_range("2020-01-01", periods=len(vals))
    return pd.DataFrame({ticker: vals}, index=idx)


def cost_series(bps, ticker="A"):
    return pd.Series({ticker: bps})


def test_entry_charged_then_flat_is_free():
    pos = make_positions([1.0] * 10)
    c = turnover_costs(pos, cost_series(10.0))
    assert np.isclose(c.iloc[0]["A"], 1.0 * 10e-4)
    assert (c.iloc[1:]["A"] == 0.0).all()


def test_daily_full_flip_hand_computed():
    pos = make_positions([1.0, -1.0, 1.0, -1.0])
    c = turnover_costs(pos, cost_series(10.0))
    assert np.isclose(c.iloc[0]["A"], 1e-3)       # entry |1-0|
    assert np.isclose(c.iloc[1]["A"], 2e-3)       # flip |−1−1| = 2
    assert np.isclose(c.iloc[2]["A"], 2e-3)
    assert np.isclose(c.iloc[3]["A"], 2e-3)


def test_zero_positions_cost_nothing():
    pos = make_positions([0.0] * 5)
    c = turnover_costs(pos, cost_series(10.0))
    assert (c == 0.0).all().all()


def test_missing_rate_raises():
    """Audit-pinned: an instrument without a cost rate must raise, not
    trade for free."""
    import pytest
    pos = make_positions([1.0, 1.0])
    with pytest.raises(ValueError, match="no cost rate"):
        turnover_costs(pos, pd.Series({"OTHER": 5.0}))


def test_per_ticker_rates_applied():
    idx = pd.bdate_range("2020-01-01", periods=2)
    pos = pd.DataFrame({"CHEAP": [1.0, 1.0], "DEAR": [1.0, 1.0]}, index=idx)
    c = turnover_costs(pos, pd.Series({"CHEAP": 1.0, "DEAR": 10.0}))
    assert np.isclose(c.iloc[0]["CHEAP"], 1e-4)
    assert np.isclose(c.iloc[0]["DEAR"], 10e-4)
