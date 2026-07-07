"""Current-state signal snapshots for the daily brief.

These reuse the exact same feature/label/eligibility code paths as the
backtested studies — the daily picks are what the backtested strategies would
hold today, not a separate ad-hoc model.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from quark import config
from quark.backtest.sizing import vol_target_positions
from quark.data.loader import compute_returns
from quark.ml.features import build_features
from quark.ml.pipeline import HGB_PARAMS
from quark.ml.targets import forward_return
from quark.ml.xsec import eligibility, rebalance_dates
from quark.strategies.classic import STRATEGIES


def multi_asset_snapshot(prices: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    """Per-instrument dashboard: recent returns, trend state, vol, and the
    vol-targeted position tsmom_252 would hold at today's close."""
    tradable = [t for t in prices.columns
                if t in universe.index and universe.at[t, "tradable"]]
    px = prices[tradable]
    rets = compute_returns(px)
    signal = STRATEGIES["tsmom_252"](px)
    positions = vol_target_positions(signal, rets)

    last = px.index[-1]
    vol63 = rets.rolling(63, min_periods=42).std() * np.sqrt(config.ANN_FACTOR)
    snap = pd.DataFrame(
        {
            "asset_class": universe.loc[tradable, "asset_class"],
            "last_price": px.loc[last],
            "ret_1d": rets.loc[last],
            "ret_5d": px.pct_change(5, fill_method=None).loc[last],
            "ret_21d": px.pct_change(21, fill_method=None).loc[last],
            "ann_vol_63d": vol63.loc[last],
            "trend_signal": signal.loc[last],
            "target_position": positions.loc[last],
        }
    )
    return snap.dropna(subset=["last_price"]).sort_values(
        ["asset_class", "target_position"], ascending=[True, False]
    )


def xsec_latest_predictions(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    top_frac: float = 0.10,
    horizon: int = config.TARGET_HORIZON,
    seed: int = config.SEED,
) -> dict:
    """Train the Study 2 model on ALL complete history (labels end `horizon`
    days before today by construction, so training can never peek past the
    prediction date) and rank today's cross-section.

    Returns {"as_of", "n_trained", "table", "longs", "shorts"}.
    """
    returns = prices.pct_change(fill_method=None)
    fwd = forward_return(returns, horizon)

    feats = build_features(prices, returns)
    calendar = feats[["month", "day_of_week"]]
    ranked = feats.drop(columns=["month", "day_of_week"]).groupby(level="date").rank(pct=True) - 0.5
    ranked[["month", "day_of_week"]] = calendar

    label = (fwd.rank(axis=1, pct=True) > 0.5).astype(float).where(fwd.notna())
    ys = label.stack().rename("y")
    ys.index.names = ["date", "ticker"]
    elig = eligibility(prices, volumes)
    es = elig.stack().rename("elig")
    es.index.names = ["date", "ticker"]

    rebal = rebalance_dates(prices.index)
    df = ranked.join(ys, how="left").join(es, how="left")
    dates_lvl = df.index.get_level_values("date")
    weekly = df[dates_lvl.isin(rebal) & df["elig"].fillna(False)].drop(columns=["elig"])

    x_cols = [c for c in weekly.columns if c != "y"]
    train = weekly.dropna(subset=["y"])  # labels stop `horizon` days ago — causal
    clf = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS)
    clf.fit(train[x_cols], train["y"].to_numpy())

    as_of = rebal[-1]
    today = weekly.xs(as_of, level="date")
    proba = clf.predict_proba(today[x_cols])[:, 1]
    table = pd.DataFrame({"prob_outperform": proba}, index=today.index)
    table["rank_pct"] = table["prob_outperform"].rank(pct=True)
    table = table.sort_values("prob_outperform", ascending=False)

    n = len(table)
    k = max(1, int(np.floor(n * top_frac)))
    return {
        "as_of": as_of,
        "n_trained": len(train),
        "n_universe": n,
        "table": table,
        "features": today[x_cols],  # per-name cross-sectional feature ranks
        "longs": list(table.index[:k]),
        "shorts": list(table.index[-k:]),
    }
