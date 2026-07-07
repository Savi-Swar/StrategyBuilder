import numpy as np
import pandas as pd
import pytest

from quark.data.loader import compute_returns
from quark.data.quality import clean_panel, quality_report


@pytest.fixture
def dates():
    return pd.bdate_range("2020-01-01", periods=300)


def test_returns_do_not_pad_across_gaps(dates):
    px = pd.Series(100.0, index=dates)
    px.iloc[50:60] = np.nan  # a 10-day hole
    r = compute_returns(px.to_frame("A"))["A"]
    # No phantom returns inside or when exiting the gap
    assert r.iloc[50:61].isna().all()


def test_stale_run_detected(dates):
    px = pd.Series(np.linspace(100, 120, len(dates)), index=dates)
    px.iloc[100:110] = 105.0  # 10 identical closes
    rep = quality_report(px.to_frame("A"))
    assert len(rep.stale_runs) == 1
    assert rep.stale_runs.iloc[0]["length"] == 10


def test_spike_and_nonpositive_flagged_and_cleaned(dates):
    px = pd.Series(50.0, index=dates)
    px.iloc[150] = -37.0  # CL=F-style negative print
    px.iloc[200] = 120.0  # +140% one-day spike, reverts next day
    px.iloc[201] = 50.0
    frame = px.to_frame("A")
    rep = quality_report(frame)
    reasons = set(rep.spikes["reason"])
    assert any(r.startswith("price<=0") for r in reasons)
    assert any(r.startswith("|ret|") for r in reasons)

    cleaned = clean_panel(frame, rep)
    assert np.isnan(cleaned.iloc[150]["A"])
    assert np.isnan(cleaned.iloc[200]["A"])
    r = compute_returns(cleaned)["A"]
    assert r.abs().max() < 0.5  # no corrupt return survives


def test_gap_detected(dates):
    px = pd.Series(100.0, index=dates)
    px.iloc[30:50] = np.nan  # 20 missing business days
    rep = quality_report(px.to_frame("A"))
    assert len(rep.gaps) == 1
    assert rep.gaps.iloc[0]["n_bdays"] == 20


def test_short_history_flagged(dates):
    panel = pd.DataFrame(
        {"OLD": 100.0, "NEW": np.nan}, index=dates, dtype=float
    )
    panel.loc[dates[-100:], "NEW"] = 50.0
    rep = quality_report(panel)
    assert rep.short_history == ["NEW"]
