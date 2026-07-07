import numpy as np
import pandas as pd

from quark.insights.brief import build_brief
from quark.insights.signals import multi_asset_snapshot


def make_universe(tickers):
    return pd.DataFrame(
        {"cost_bps": 5.0, "tradable": True, "asset_class": "stock"},
        index=pd.Index(tickers, name="ticker"),
    )


def synthetic_panel(n=400, seed=9):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2023-01-02", periods=n)
    return pd.DataFrame(
        {c: 100 * np.cumprod(1 + rng.normal(0.0004, 0.01, n)) for c in ["AAA", "BBB"]},
        index=idx,
    )


def test_multi_asset_snapshot_shape_and_bounds():
    prices = synthetic_panel()
    snap = multi_asset_snapshot(prices, make_universe(["AAA", "BBB"]))
    assert set(snap.index) == {"AAA", "BBB"}
    assert snap["trend_signal"].isin([-1.0, 0.0, 1.0]).all()
    assert (snap["target_position"].abs() <= 4.0).all()  # leverage cap respected
    assert (snap["ann_vol_63d"] > 0).all()


def test_build_brief_renders_without_llm_or_news():
    prices = synthetic_panel()
    snap = multi_asset_snapshot(prices, make_universe(["AAA", "BBB"]))
    xsec = {
        "as_of": prices.index[-1],
        "n_trained": 1000,
        "n_universe": 2,
        "table": pd.DataFrame({"prob_outperform": [0.61, 0.42]},
                              index=["AAA", "BBB"]),
        "longs": ["AAA"],
        "shorts": ["BBB"],
    }
    md = build_brief(snap, xsec, headlines={}, commentary=None)
    assert "Quark Daily Brief" in md
    assert "AAA" in md and "BBB" in md
    assert "Not investment advice" in md
    assert "Analyst commentary" not in md  # section absent when no LLM
