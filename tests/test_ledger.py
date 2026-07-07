import numpy as np
import pandas as pd
import pytest

import quark.insights.ledger as ledger


@pytest.fixture
def tmp_ledger(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger, "LEDGER_DIR", tmp_path)
    monkeypatch.setattr(ledger, "PRED_PATH", tmp_path / "predictions.csv")
    monkeypatch.setattr(ledger, "IC_PATH", tmp_path / "ic_history.csv")
    return tmp_path


def panel_with_predictable_winners(n_days=60, n_stocks=60, seed=3):
    """Stocks 0..29 drift up, 30..59 drift down — a knowable cross-section."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2024-01-01", periods=n_days)
    cols = [f"S{i}" for i in range(n_stocks)]
    drifts = np.array([0.004] * (n_stocks // 2) + [-0.004] * (n_stocks // 2))
    data = 100 * np.cumprod(1 + rng.normal(drifts, 0.005, (n_days, n_stocks)), axis=0)
    return pd.DataFrame(data, index=idx, columns=cols)


def test_record_is_idempotent(tmp_ledger):
    probs = pd.Series([0.6, 0.4], index=["A", "B"])
    as_of = pd.Timestamp("2024-03-01")
    assert ledger.record_predictions(as_of, probs) is True
    assert ledger.record_predictions(as_of, probs) is False  # duplicate date


def test_realized_ic_positive_for_correct_predictions(tmp_ledger):
    prices = panel_with_predictable_winners()
    as_of = prices.index[20]
    # predictions aligned with the true drifts
    probs = pd.Series([0.7] * 30 + [0.3] * 30, index=prices.columns)
    ledger.record_predictions(as_of, probs)

    ic = ledger.update_realized(prices)
    assert len(ic) == 1
    assert ic.iloc[0]["ic"] > 0.3
    assert ic.iloc[0]["decile_spread"] > 0
    assert ic.iloc[0]["horizon"] == 5

    ic2 = ledger.update_realized(prices)  # idempotent
    assert len(ic2) == 1

    # a second horizon on the same date is its own ledger entry
    ledger.record_predictions(as_of, probs, horizon=21)
    ic3 = ledger.update_realized(prices)
    assert len(ic3) == 2 and set(ic3["horizon"]) == {5, 21}


def test_unscoreable_recent_date_waits(tmp_ledger):
    prices = panel_with_predictable_winners()
    probs = pd.Series(0.5, index=prices.columns)
    ledger.record_predictions(prices.index[-2], probs)  # horizon incomplete
    ic = ledger.update_realized(prices)
    assert ic.empty


def test_health_states(tmp_ledger):
    today = pd.Timestamp.today().normalize()
    # warming: too few observations
    few = pd.DataFrame({"as_of": pd.bdate_range("2025-01-03", periods=3, freq="W-FRI"),
                        "ic": [0.02, 0.01, 0.03], "decile_spread": [0.001] * 3,
                        "n": [400] * 3, "source": ["walkforward"] * 3})
    h = ledger.health_summary(few, data_through=today)
    assert h["model_status"] == "warming"

    def hist(vals):
        n = len(vals)
        return pd.DataFrame({"as_of": pd.bdate_range("2024-01-05", periods=n, freq="W-FRI"),
                             "ic": vals, "decile_spread": [0.001] * n,
                             "n": [400] * n, "source": ["walkforward"] * n})

    rng = np.random.default_rng(0)
    good = ledger.health_summary(hist(rng.normal(0.03, 0.02, 30)), data_through=today)
    assert good["model_status"] == "green"

    bad = ledger.health_summary(hist(rng.normal(-0.04, 0.02, 30)), data_through=today)
    assert bad["model_status"] == "red"

    stale = ledger.health_summary(hist(rng.normal(0.03, 0.02, 30)),
                                  data_through=today - pd.Timedelta(days=20))
    assert stale["data_status"] == "red"
