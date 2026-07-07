import numpy as np
import pandas as pd
import pytest

import quark.insights.ledger as ledger
import quark.insights.review as review_mod
from quark.insights.review import build_review
from quark.reports.review_page import render_review_page


@pytest.fixture
def tmp_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    monkeypatch.setattr(ledger, "PRED_PATH", tmp_path / "predictions.csv")
    monkeypatch.setattr(ledger, "IC_PATH", tmp_path / "ic_history.csv")
    monkeypatch.setattr(review_mod, "PRED_PATH", tmp_path / "predictions.csv")
    return tmp_path


def seeded_history(tmp_ledger, n_weeks=12, n_stocks=60, seed=4):
    """Panel where half the stocks drift up, half down, and predictions
    aligned with truth — top-3 grading should come out strongly positive."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=n_weeks * 5 + 30)
    cols = [f"S{i}" for i in range(n_stocks)]
    drifts = np.array([0.003] * (n_stocks // 2) + [-0.003] * (n_stocks // 2))
    prices = pd.DataFrame(
        100 * np.cumprod(1 + rng.normal(drifts, 0.004, (len(idx), n_stocks)), axis=0),
        index=idx, columns=cols)
    base = np.linspace(0.72, 0.28, n_stocks)  # unique, ordered probs
    for w in range(n_weeks):
        as_of = idx[10 + w * 5]
        probs = pd.Series(base + rng.normal(0, 0.005, n_stocks), index=cols)
        ledger.record_predictions(as_of, probs, source="walkforward")
    return prices


def test_review_grades_correct_predictions_as_wins(tmp_ledger):
    prices = seeded_history(tmp_ledger)
    review = build_review(prices, weeks=52)
    trades, s = review["trades"], review["summary"]

    assert s["n_weeks"] >= 10
    assert len(trades) == s["n_trades"] == s["n_weeks"] * 3
    assert s["hit_rel"] > 0.8            # aligned predictions must grade well
    assert s["avg_rel_bps"] > 0
    sides = set(trades["side"])
    assert "LONG" in sides and "SHORT" in sides
    assert len(review["lessons"]) >= 2
    # a winning SHORT must have rel_5d > 0 while its raw return is negative
    shorts = trades[trades["side"] == "SHORT"]
    assert (shorts["ret_5d"].mean() < 0) and (shorts["rel_5d"].mean() > 0)


def test_review_page_renders(tmp_ledger):
    prices = seeded_history(tmp_ledger)
    review = build_review(prices, weeks=52)
    html = render_review_page(review, "2026-07-07T08:00:00")
    assert "Past Trades" in html
    assert "WIN" in html and "Grade" in html
    assert "back to desk" in html


def test_review_empty_ledger_is_graceful(tmp_ledger):
    prices = pd.DataFrame(
        {"A": 100.0}, index=pd.bdate_range("2024-01-01", periods=30))
    review = build_review(prices)
    assert review["trades"].empty
    html = render_review_page(review, "2026-07-07T08:00:00")
    assert "No scored history" in html
