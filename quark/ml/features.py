"""Feature engineering for the ML studies.

All features at date t use information through t ONLY — enforced by a
truncation-invariance unit test (features on a truncated panel must equal
features on the full panel at the truncation date).

Output is long format with MultiIndex (date, ticker). No scaling/imputation:
HistGradientBoosting handles NaNs natively and is scale-invariant, and every
scaler fitted on pooled data is a potential leak vector.
"""

import numpy as np
import pandas as pd

from quark.strategies.classic import rsi

MOM_HORIZONS = (5, 21, 63, 126, 252)


def build_features(
    prices: pd.DataFrame,
    returns: pd.DataFrame | None = None,
    universe: pd.DataFrame | None = None,
    market_ticker: str = "^GSPC",
    rate_ticker: str = "^TNX",
) -> pd.DataFrame:
    if returns is None:
        returns = prices.pct_change(fill_method=None)

    vol21 = returns.rolling(21, min_periods=21).std()
    vol63 = returns.rolling(63, min_periods=42).std()
    vol252 = returns.rolling(252, min_periods=126).std()

    feats: dict[str, pd.DataFrame] = {}
    for h in MOM_HORIZONS:
        feats[f"mom_{h}"] = prices.pct_change(h, fill_method=None) / (
            vol21 * np.sqrt(h)
        )
    feats["vol_ratio_21_63"] = vol21 / vol63
    feats["vol_ratio_63_252"] = vol63 / vol252
    feats["rsi_14"] = (rsi(prices, 14) - 50.0) / 50.0
    feats["dist_52w_high"] = prices / prices.rolling(252, min_periods=200).max() - 1.0
    # Cross-sectional rank across instruments alive that day (NaNs excluded
    # by rank); computed on the wide frame so the rank universe is per-date.
    feats["xsec_rank_mom_21"] = feats["mom_21"].rank(axis=1, pct=True)

    long = pd.concat(
        {name: f.stack() for name, f in feats.items()}, axis=1
    )
    long.index.names = ["date", "ticker"]

    dates = long.index.get_level_values("date")
    long["month"] = dates.month
    long["day_of_week"] = dates.dayofweek

    # Market context, broadcast to every row by date. This is where the
    # non-tradable ^TNX yield series earns its keep.
    ctx = {}
    if market_ticker in prices.columns:
        ctx["mkt_mom_21"] = feats["mom_21"][market_ticker]
    if rate_ticker in prices.columns:
        ctx["rate_chg_63"] = prices[rate_ticker].diff(63)
    if ctx:
        ctx_df = pd.DataFrame(ctx)
        ctx_df.index.name = "date"
        long = long.join(ctx_df, on="date")

    if universe is not None:
        classes = universe["asset_class"].astype("category").cat.codes
        long["asset_class_code"] = (
            long.index.get_level_values("ticker").map(classes).astype(float)
        )

    return long
