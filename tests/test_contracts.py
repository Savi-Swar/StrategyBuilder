"""Every production data artifact this repo has hit, pinned as a regression
test against the ingest contracts. If one of these passes validation, the
contract has regressed."""
import numpy as np
import pandas as pd
import pytest

from quark.data.contracts import (ContractError, validate_ann_dates,
                                  validate_ohlcv_ingest, validate_price_panel)


def ohlcv(rows):
    return pd.DataFrame(rows, columns=["ticker", "date", "open", "high",
                                       "low", "close", "volume"])


def test_negative_wti_close_rejected():
    """2020-04-20: CL=F settled at −$37.63. A nonpositive close must never
    enter the stocks table as a price."""
    df = ohlcv([("CL=F", "2020-04-17", 18.0, 18.3, 17.5, 18.27, 100),
                ("CL=F", "2020-04-20", 17.7, 17.9, -40.3, -37.63, 100)])
    with pytest.raises(ContractError, match="close"):
        validate_ohlcv_ingest(df)


def test_duplicate_ticker_date_rejected():
    df = ohlcv([("AAPL", "2026-01-05", 1.0, 1.0, 1.0, 1.0, 10),
                ("AAPL", "2026-01-05", 1.0, 1.0, 1.0, 1.0, 10)])
    with pytest.raises(ContractError):
        validate_ohlcv_ingest(df)


def test_clean_ingest_passes():
    df = ohlcv([("AAPL", "2026-01-05", 1.0, 1.1, 0.9, 1.05, 10),
                ("AAPL", "2026-01-06", 1.05, 1.2, 1.0, 1.10, 12)])
    out = validate_ohlcv_ingest(df)
    assert len(out) == 2


def test_ticker_reuse_spike_rejected():
    """The +17,000,000% artifact: a delisted symbol reassigned to a different
    company shows up as an absurd one-day 'return'. The panel contract must
    treat any move beyond ±200%/day as an identity break."""
    idx = pd.bdate_range("2026-01-05", periods=4)
    panel = pd.DataFrame({"GOOD": [10.0, 10.1, 10.05, 10.2],
                          "REUSED": [0.02, 0.02, 3400.0, 3390.0]}, index=idx)
    with pytest.raises(ContractError, match="spike"):
        validate_price_panel(panel)


def test_normal_volatility_passes():
    idx = pd.bdate_range("2026-01-05", periods=5)
    rng = np.random.default_rng(7)
    panel = pd.DataFrame(
        {t: 100 * np.cumprod(1 + rng.normal(0, 0.05, 5)) for t in ("A", "B")},
        index=idx)
    assert validate_price_panel(panel) is panel


def test_unsorted_panel_rejected():
    idx = pd.to_datetime(["2026-01-06", "2026-01-05"])
    panel = pd.DataFrame({"A": [1.0, 1.0]}, index=idx)
    with pytest.raises(ContractError, match="sorted"):
        validate_price_panel(panel)


def test_ann_dates_contract():
    ok = pd.DataFrame({"ticker": ["AAPL", "BRK-B"],
                       "ann_date": ["2026-04-30", "2026-05-02"]})
    assert len(validate_ann_dates(ok)) == 2
    bad = pd.DataFrame({"ticker": ["aapl"], "ann_date": ["04/30/2026"]})
    with pytest.raises(ContractError):
        validate_ann_dates(bad)
