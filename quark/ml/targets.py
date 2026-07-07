"""Forward-return targets. The alignment here is THE classic silent leak —
it is pinned down by a hand-built unit test in tests/test_targets.py.

Target at date t covers (t, t+h]: the compounded return of the h bars AFTER t.
Implemented as log1p-rolling-sum shifted by -h: the rolling sum at t+h covers
[t+1, t+h], and shift(-h) places it at t.
"""

import numpy as np
import pandas as pd


def forward_return(returns: pd.DataFrame, horizon: int = 5) -> pd.DataFrame:
    log_fwd = np.log1p(returns).rolling(horizon, min_periods=horizon).sum().shift(-horizon)
    return np.expm1(log_fwd)


def build_target(
    returns: pd.DataFrame, horizon: int = 5, vol_lookback: int = 21
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (vol-normalized forward return, binary up/down label)."""
    fwd = forward_return(returns, horizon)
    vol = returns.rolling(vol_lookback, min_periods=vol_lookback).std()
    norm = fwd / (vol * np.sqrt(horizon))
    label = (norm > 0).astype(float).where(norm.notna())
    return norm, label
