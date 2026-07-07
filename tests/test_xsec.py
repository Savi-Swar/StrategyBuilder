import numpy as np
import pandas as pd

from quark.ml.xsec import _decile_weights, eligibility, rebalance_dates


def test_decile_weights_dollar_neutral_and_gross_one():
    preds = pd.Series(np.linspace(0.3, 0.7, 20), index=[f"S{i}" for i in range(20)])
    w = _decile_weights(preds, top_frac=0.10)
    assert np.isclose(w.sum(), 0.0)          # dollar-neutral
    assert np.isclose(w.abs().sum(), 1.0)    # 100% gross
    assert (w > 0).sum() == 2 and (w < 0).sum() == 2  # top/bottom 2 of 20
    assert w["S19"] > 0 and w["S0"] < 0


def test_rebalance_dates_are_week_ends():
    idx = pd.bdate_range("2021-01-04", "2021-03-31")
    rd = rebalance_dates(idx)
    # All Fridays in a holiday-free stretch, except the final partial week
    assert (rd[:-1].weekday == 4).all()
    assert rd.isin(idx).all()
    assert len(rd) == len(idx.isocalendar().week.unique())


def test_eligibility_is_causal_and_filters():
    idx = pd.bdate_range("2020-01-01", periods=300)
    prices = pd.DataFrame({"GOOD": 50.0, "PENNY": 2.0}, index=idx)
    volumes = pd.DataFrame({"GOOD": 1e6, "PENNY": 1e6}, index=idx)
    elig = eligibility(prices, volumes, min_history=252)
    assert not elig["PENNY"].any()               # price filter
    assert not elig["GOOD"].iloc[:251].any()     # history filter is causal
    assert elig["GOOD"].iloc[260:].all()
