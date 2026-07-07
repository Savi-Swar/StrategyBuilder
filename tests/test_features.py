import numpy as np
import pandas as pd

from quark.ml.features import build_features


def synthetic_prices(n=420, n_assets=3, seed=5):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2018-01-01", periods=n)
    data = {
        f"T{i}": 100 * np.cumprod(1 + rng.normal(0.0002, 0.01, n))
        for i in range(n_assets)
    }
    return pd.DataFrame(data, index=idx)


def test_features_are_truncation_invariant():
    """A feature at date t must not change when future prices change.
    Computing on a truncated panel and on the full panel must agree at the
    truncation date — the definitive no-lookahead check for features."""
    prices = synthetic_prices()
    k = 350
    f_full = build_features(prices)
    f_trunc = build_features(prices.iloc[:k])
    d = prices.index[k - 1]
    pd.testing.assert_frame_equal(
        f_full.xs(d, level="date"), f_trunc.xs(d, level="date")
    )


def test_warmup_rows_are_nan():
    prices = synthetic_prices()
    f = build_features(prices)
    dates = f.index.get_level_values("date")
    assert f[dates < prices.index[252]]["mom_252"].isna().all()
    # dist_52w_high warms up at its min_periods (200 observations)
    assert f[dates < prices.index[199]]["dist_52w_high"].isna().all()


def test_xsec_rank_spans_alive_universe_only():
    prices = synthetic_prices(n_assets=4)
    prices.iloc[:, 3] = np.nan  # T3 never alive
    f = build_features(prices)
    last = f.xs(prices.index[-1], level="date")
    ranks = last["xsec_rank_mom_21"].dropna()
    # pct ranks over the 3 alive assets: max must be 1.0, min 1/3
    assert np.isclose(ranks.max(), 1.0)
    assert np.isclose(ranks.min(), 1 / 3)
