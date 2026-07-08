"""Transaction costs charged on turnover."""

import pandas as pd


def turnover_costs(positions: pd.DataFrame, cost_bps: pd.Series) -> pd.DataFrame:
    """Cost at t = |position change at t| * per-instrument bps.

    The first bar charges the full entry (|pos - 0|): entering a position is
    not free. `cost_bps` is indexed by ticker (see quark.universe).
    """
    dpos = positions.diff()
    if len(dpos):
        dpos.iloc[0] = positions.iloc[0]
    rate = cost_bps.reindex(positions.columns) * 1e-4
    if rate.isna().any():
        missing = list(rate.index[rate.isna()])
        raise ValueError(f"no cost rate for {missing} — silent free trading "
                         "is how backtests lie")
    return dpos.abs().mul(rate, axis=1).fillna(0.0)
