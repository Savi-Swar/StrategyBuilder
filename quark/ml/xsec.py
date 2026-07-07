"""Study 2: cross-sectional long-short US equity strategy (the flagship).

Weekly cadence: at each rebalance date, rank all eligible stocks by
ML-predicted probability of beating the cross-sectional median over the next
5 trading days; go long the top decile, short the bottom decile,
equal-weighted within legs, dollar-neutral, 100% gross exposure.

Methodology guardrails:
- Features are per-date cross-sectional ranks (leak-proof by construction:
  a rank at date t only involves date-t values).
- Label is relative (above/below cross-sectional median forward return), so
  the model predicts WINNERS VS LOSERS, not the market.
- Eligibility (price, dollar volume, history) is evaluated causally at each
  rebalance date.
- Same PurgedWalkForward splitter as Study 1; purge >= horizon.
- KNOWN BIAS: the universe is TODAY'S S&P 500 members (survivorship).
  Documented in RESEARCH_NOTES.md; the long-short spread nets out part of
  the common uplift, but results should be read as upper bounds.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

from quark import config
from quark.ml.features import build_features
from quark.ml.pipeline import HGB_PARAMS
from quark.ml.splits import PurgedWalkForward
from quark.ml.targets import forward_return


@dataclass
class XSecResult:
    weights: pd.DataFrame        # daily weight panel (ffilled between rebalances)
    predictions: pd.DataFrame    # rebalance-date x ticker OOS probabilities
    fold_stats: pd.DataFrame
    ic: pd.Series                # per-rebalance-date Spearman IC (pred vs realized)
    decile_means: pd.Series      # mean gross fwd return per prediction decile


def rebalance_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each week."""
    s = pd.Series(index, index=index)
    return pd.DatetimeIndex(s.resample("W-FRI").last().dropna().values)


def eligibility(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    min_price: float = 5.0,
    min_dollar_vol: float = 5e6,
    min_history: int = 252,
) -> pd.DataFrame:
    """Causal per-date tradability mask."""
    dollar_vol = (prices * volumes).rolling(63, min_periods=21).median()
    enough_history = prices.notna().cumsum() >= min_history
    return (prices > min_price) & (dollar_vol > min_dollar_vol) & enough_history


def _decile_weights(preds_row: pd.Series, top_frac: float) -> pd.Series:
    r = preds_row.rank(pct=True)
    long = r > 1.0 - top_frac   # strict: symmetric leg sizes at the boundary
    short = r <= top_frac
    w = pd.Series(0.0, index=preds_row.index)
    if long.sum() and short.sum():
        w[long] = 0.5 / long.sum()      # +50% gross long
        w[short] = -0.5 / short.sum()   # -50% gross short
    return w


def run_xsec_strategy(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    *,
    horizon: int = config.TARGET_HORIZON,
    top_frac: float = 0.10,
    rebal_every: int = 1,
    seed: int = config.SEED,
    shuffle_labels: bool = False,
) -> XSecResult:
    returns = prices.pct_change(fill_method=None)
    fwd = forward_return(returns, horizon)

    # Cross-sectional rank features per date, centered at 0.
    feats = build_features(prices, returns)  # no universe/context columns
    calendar = feats[["month", "day_of_week"]]
    ranked = feats.drop(columns=["month", "day_of_week"]).groupby(level="date").rank(pct=True) - 0.5
    ranked[["month", "day_of_week"]] = calendar

    # Relative label: above cross-sectional median forward return.
    label = (fwd.rank(axis=1, pct=True) > 0.5).astype(float).where(fwd.notna())

    rebal = rebalance_dates(prices.index)[::rebal_every]
    elig = eligibility(prices, volumes)

    ys = label.stack().rename("y")
    ys.index.names = ["date", "ticker"]
    es = elig.stack().rename("elig")
    es.index.names = ["date", "ticker"]
    df = ranked.join(ys, how="inner").dropna(subset=["y"])
    df = df.join(es, how="left")
    dates_lvl = df.index.get_level_values("date")
    df = df[dates_lvl.isin(rebal) & df["elig"].fillna(False)]
    df = df.drop(columns=["elig"])

    x_cols = [c for c in df.columns if c != "y"]
    fold_dates = df.index.get_level_values("date")
    rng = np.random.default_rng(seed)

    fold_rows, pred_parts = [], []
    # purge must scale with the label horizon or long-horizon labels leak
    wf = PurgedWalkForward(prices.index,
                           purge=max(config.PURGE_DAYS, horizon),
                           embargo=config.EMBARGO_DAYS)
    for train_dates, test_dates in wf.split():
        tr = df[fold_dates.isin(train_dates)]
        te = df[fold_dates.isin(test_dates)]
        if tr.empty or te.empty:
            continue
        y_tr = tr["y"].to_numpy()
        if shuffle_labels:
            y_tr = rng.permutation(y_tr)
        clf = HistGradientBoostingClassifier(random_state=seed, **HGB_PARAMS)
        clf.fit(tr[x_cols], y_tr)
        proba = clf.predict_proba(te[x_cols])[:, 1]
        auc = roc_auc_score(te["y"], proba) if te["y"].nunique() > 1 else np.nan
        fold_rows.append(
            {
                "year": test_dates[0].year,
                "n_train": len(tr),
                "n_test": len(te),
                "n_stocks_median": int(te.groupby(level="date").size().median()),
                "auc": auc,
                "base_rate": float(te["y"].mean()),
            }
        )
        pred_parts.append(pd.Series(proba, index=te.index))

    predictions = pd.concat(pred_parts).unstack("ticker")

    # Portfolio weights: dollar-neutral extreme deciles, ffilled to daily.
    weights_rebal = predictions.apply(_decile_weights, axis=1, top_frac=top_frac)
    weights = (
        weights_rebal.reindex(prices.index)
        .ffill(limit=7 * rebal_every)
        .fillna(0.0)
    )

    # Information coefficient: Spearman = Pearson on ranks, per rebalance date.
    fwd_at_rebal = fwd.reindex(predictions.index)[predictions.columns]
    ic = (
        predictions.rank(axis=1)
        .corrwith(fwd_at_rebal.rank(axis=1), axis=1)
        .dropna()
    )

    # Decile spread: mean gross forward return per prediction decile.
    pred_rank = predictions.rank(axis=1, pct=True)
    deciles = np.ceil(pred_rank * 10).clip(1, 10)
    decile_means = (
        pd.DataFrame(
            {"decile": deciles.stack(), "fwd": fwd_at_rebal.stack()}
        )
        .dropna()
        .groupby("decile")["fwd"]
        .mean()
    )

    return XSecResult(weights, predictions, pd.DataFrame(fold_rows), ic, decile_means)
