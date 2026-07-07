"""Volatility-targeted position sizing."""

import numpy as np
import pandas as pd

from quark import config


def vol_target_positions(
    signals: pd.DataFrame,
    returns: pd.DataFrame,
    vol_target: float = config.VOL_TARGET,
    lookback: int = config.VOL_LOOKBACK,
    max_leverage: float = config.MAX_LEVERAGE,
    min_periods: int | None = None,
) -> pd.DataFrame:
    """Scale signals in [-1, 1] to positions targeting `vol_target` annualized
    vol per instrument, capped at `max_leverage`.

    The vol estimate at t uses returns through t; causality is enforced by the
    engine shifting the entire scaled panel by the execution lag. The leverage
    cap is essential: managed/low-vol regimes (THB=X, KRW=X) otherwise produce
    exploding vol_target/vol ratios.
    """
    if min_periods is None:
        min_periods = max(20, (2 * lookback) // 3)
    vol = returns.rolling(lookback, min_periods=min_periods).std() * np.sqrt(config.ANN_FACTOR)
    with np.errstate(divide="ignore", invalid="ignore"):
        leverage = (vol_target / vol).clip(upper=max_leverage)
    return (signals * leverage).fillna(0.0)
