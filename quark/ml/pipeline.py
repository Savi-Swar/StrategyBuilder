"""Walk-forward ML pipeline for Study 1 (multi-asset timing).

Design choices that matter:
- Fixed hyperparameters. Tuning them inside the walk-forward is a time sink
  and reintroduces the multiple-testing sin; the registry-counting discipline
  applies to ML configs too.
- No imputation, no scaling — HistGradientBoosting handles NaN natively and
  is scale-invariant, and every fitted preprocessor is a potential leak.
- shuffle_labels=True trains on permuted labels: AUC must collapse to ~0.5
  and the strategy Sharpe to ~0, or something is leaking.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score

from quark import config
from quark.ml.features import build_features
from quark.ml.splits import PurgedWalkForward
from quark.ml.targets import build_target

HGB_PARAMS = dict(
    max_depth=3,
    learning_rate=0.05,
    max_iter=300,
    l2_regularization=1.0,
    early_stopping=False,
)


def _calibrate_signal(raw: pd.DataFrame, window: int = 252,
                      min_periods: int = 60) -> pd.DataFrame:
    """Causal amplitude calibration: classifier probabilities cluster near
    0.5, so raw 2p-1 signals have magnitude ~0.05 and positions run far below
    the vol target while still paying full turnover costs. Normalize each
    instrument's forecast by its own TRAILING forecast std (past OOS
    forecasts only — no lookahead), then clip to [-1, 1]. One fixed design
    decision, made a priori, not tuned."""
    scale = raw.rolling(window, min_periods=min_periods).std()
    return (raw / scale).clip(-1.0, 1.0)


@dataclass
class MLResult:
    signals: pd.DataFrame            # date x ticker in [-1, 1], OOS only
    fold_stats: pd.DataFrame         # year, n_train, n_test, auc, base_rate
    importance: pd.DataFrame | None  # permutation importance, last fold


def run_ml_strategy(
    prices: pd.DataFrame,
    universe: pd.DataFrame | None = None,
    horizon: int = config.TARGET_HORIZON,
    seed: int = config.SEED,
    shuffle_labels: bool = False,
    compute_importance: bool = True,
) -> MLResult:
    returns = prices.pct_change(fill_method=None)
    features = build_features(prices, returns, universe)
    _, label = build_target(returns, horizon)

    ys = label.stack().rename("y")
    ys.index.names = ["date", "ticker"]
    df = features.join(ys, how="inner").dropna(subset=["y"])

    if universe is not None:
        # Train and predict only on instruments we would actually trade:
        # tradability excludes ^TNX; hindsight-picked stocks stay out of the
        # headline study on both sides of the model.
        ok = universe.index[universe["tradable"] & ~universe.get(
            "hindsight_picked", pd.Series(False, index=universe.index))]
        df = df[df.index.get_level_values("ticker").isin(ok)]

    x_cols = [c for c in df.columns if c != "y"]
    fold_dates = df.index.get_level_values("date")
    rng = np.random.default_rng(seed)

    fold_rows, sig_parts, clf, te = [], [], None, None
    for train_dates, test_dates in PurgedWalkForward(prices.index).split():
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
                "auc": auc,
                "base_rate": float(te["y"].mean()),
            }
        )
        sig_parts.append(pd.Series(2.0 * proba - 1.0, index=te.index))

    raw = pd.concat(sig_parts).unstack("ticker")
    # Hold positions through label-less days (local holidays): a 1-day NaN
    # signal would otherwise close and reopen the position, paying 2x costs.
    signals = _calibrate_signal(raw).ffill(limit=5)

    importance = None
    if compute_importance and clf is not None and not shuffle_labels:
        pi = permutation_importance(
            clf, te[x_cols], te["y"], n_repeats=5, random_state=seed
        )
        importance = (
            pd.DataFrame({"importance": pi.importances_mean}, index=x_cols)
            .sort_values("importance", ascending=False)
        )

    return MLResult(signals, pd.DataFrame(fold_rows), importance)
