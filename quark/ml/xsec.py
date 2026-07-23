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
from quark.data.loader import compute_returns
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


def apply_membership(elig: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    """AND point-in-time membership snapshots into eligibility.

    Snapshots may sit on non-trading dates (calendar month-ends — ~2/7 land
    on weekends). Reindexing straight to trading days would DROP those rows
    and ffill across them, leaving membership stale by an extra month; align
    on the union of both calendars first so every snapshot governs the
    trading days that follow it. Before the first snapshot: not a member.
    """
    m = membership.astype(float)
    m = m.reindex(m.index.union(elig.index)).ffill()
    return elig & (m.reindex(index=elig.index, columns=elig.columns)
                   .fillna(0.0).astype(bool))


def hysteresis_weights(predictions: pd.DataFrame, exit_gap: float) -> pd.DataFrame:
    """No-trade-band book: ENTER in the extreme decile (same boundary as
    `_decile_weights`), EXIT only once the name's cross-sectional rank has
    decayed past `exit_gap` (or it leaves the prediction universe). Sides
    stay equal-weighted at ±50% gross, so only the churn rule differs from
    weekly re-formation."""
    longs: set = set()
    shorts: set = set()
    rows = {}
    for dt, row in predictions.iterrows():
        pct = row.rank(pct=True).dropna()
        longs = {t for t in longs
                 if t in pct.index and pct[t] > 0.90 - exit_gap}
        shorts = {t for t in shorts
                  if t in pct.index and pct[t] <= 0.10 + exit_gap}
        longs |= set(pct.index[pct > 0.90])
        shorts |= set(pct.index[pct <= 0.10])
        w = pd.Series(0.0, index=predictions.columns)
        if longs and shorts:
            w[list(longs)] = 0.5 / len(longs)
            w[list(shorts)] = -0.5 / len(shorts)
        rows[dt] = w
    return pd.DataFrame(rows).T


def partial_rebalance_weights(target_weights: pd.DataFrame, tau: float) -> pd.DataFrame:
    """Garleanu-Pedersen-style partial trading: at each rebalance move a
    fraction `tau` from the held book toward that date's target book
    (tau=1.0 reproduces full weekly re-formation). The held book is an EWMA
    of past targets, so turnover falls with tau and the book tilts toward
    the persistent component of the signal — the construction-time cost
    lever documented in reports/deep_research_net_alpha_2026-07-22.md.
    Names leaving the target book decay geometrically instead of being
    dumped in one trade. Dollar neutrality is preserved (EWMA of neutral
    books is neutral); gross exposure ends below 1.0, which is fine for
    Sharpe comparisons since returns and linear costs scale together."""
    held = pd.Series(0.0, index=target_weights.columns)
    rows = {}
    for dt, target in target_weights.iterrows():
        held = held + tau * (target.fillna(0.0) - held)
        rows[dt] = held.copy()
    return pd.DataFrame(rows).T


def run_xsec_strategy(
    prices: pd.DataFrame,
    volumes: pd.DataFrame,
    *,
    horizon: int = config.TARGET_HORIZON,
    top_frac: float = 0.10,
    rebal_every: int = 1,
    seed: int = config.SEED,
    shuffle_labels: bool = False,
    membership: pd.DataFrame | None = None,
    extra_features: dict[str, pd.DataFrame] | None = None,
    elig_kwargs: dict | None = None,
) -> XSecResult:
    returns = compute_returns(prices)
    fwd = forward_return(returns, horizon)

    # Cross-sectional rank features per date, centered at 0.
    feats = build_features(prices, returns)  # no universe/context columns
    calendar = feats[["month", "day_of_week"]]
    ranked = feats.drop(columns=["month", "day_of_week"]).groupby(level="date").rank(pct=True) - 0.5
    ranked[["month", "day_of_week"]] = calendar
    if extra_features:
        # Same treatment as the built-ins: per-date cross-sectional rank.
        # Caller owns PIT-correctness of the panels (values must be known
        # on the date they appear — see quark/data/edgar.py).
        for name, panel in extra_features.items():
            extra = (panel.rank(axis=1, pct=True) - 0.5).stack()
            extra.index.names = ["date", "ticker"]
            ranked[name] = extra

    # Relative label: above cross-sectional median forward return.
    label = (fwd.rank(axis=1, pct=True) > 0.5).astype(float).where(fwd.notna())

    rebal = rebalance_dates(prices.index)[::rebal_every]
    elig = eligibility(prices, volumes, **(elig_kwargs or {}))
    if membership is not None:
        elig = apply_membership(elig, membership)

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
