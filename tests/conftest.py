"""Shared synthetic fixtures. NO test touches the real database — CI must run
on a bare checkout."""

import pandas as pd
import pytest


def make_universe(tickers, cost_bps=10.0, tradable=True) -> pd.DataFrame:
    return pd.DataFrame(
        {"cost_bps": cost_bps, "tradable": tradable},
        index=pd.Index(tickers, name="ticker"),
    )


@pytest.fixture
def bdates():
    return pd.bdate_range("2019-01-01", periods=300)
