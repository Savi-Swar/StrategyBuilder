import numpy as np
import pandas as pd

from quark.ml.targets import build_target, forward_return


def test_target_window_is_strictly_future():
    """Target at t covers (t, t+5] — never t itself. THE off-by-one test."""
    idx = pd.bdate_range("2020-01-01", periods=30)
    r = pd.DataFrame(0.0, index=idx, columns=["A"])
    r.iloc[11] = 0.10  # single big return at position 11

    fwd = forward_return(r, horizon=5)
    assert np.isclose(fwd.iloc[6]["A"], 0.10)   # window (6, 11] includes it
    assert np.isclose(fwd.iloc[10]["A"], 0.10)  # window (10, 15] includes it
    assert np.isclose(fwd.iloc[5]["A"], 0.0)    # window (5, 10] does not
    assert np.isclose(fwd.iloc[11]["A"], 0.0)   # its OWN day must not count
    assert fwd.iloc[-5:]["A"].isna().all()      # tail undefined


def test_forward_return_compounds():
    idx = pd.bdate_range("2020-01-01", periods=20)
    r = pd.DataFrame(0.01, index=idx, columns=["A"])
    fwd = forward_return(r, horizon=5)
    assert np.isclose(fwd.iloc[0]["A"], 1.01**5 - 1)


def test_label_is_binary_and_nan_preserving():
    idx = pd.bdate_range("2020-01-01", periods=60)
    rng = np.random.default_rng(0)
    r = pd.DataFrame(rng.normal(0, 0.01, (60, 1)), index=idx, columns=["A"])
    norm, label = build_target(r, horizon=5, vol_lookback=21)
    valid = label["A"].dropna()
    assert set(valid.unique()) <= {0.0, 1.0}
    assert label["A"].iloc[-5:].isna().all()
    assert (norm["A"].dropna().index == valid.index).all()
