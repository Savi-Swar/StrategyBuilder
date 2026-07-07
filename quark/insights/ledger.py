"""Prediction ledger and model-health monitoring.

Every prediction Vig makes is recorded; once its 5-day horizon has passed,
it is scored against realized returns. The ledger is seeded with genuine
walk-forward (out-of-sample) predictions from the backtest, so the health
panel has real history from day one. This is the discipline that separates
"the backtest said 0.017" from "the model is still delivering 0.017":
the edge is only as real as its live track record.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.ml.targets import forward_return

LEDGER_DIR = config.REPORTS_DIR / "ledger"
PRED_PATH = LEDGER_DIR / "predictions.csv"
IC_PATH = LEDGER_DIR / "ic_history.csv"


def _load(path, parse=("as_of",)) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, parse_dates=list(parse))


def record_predictions(as_of: pd.Timestamp, probs: pd.Series,
                       source: str = "live") -> bool:
    """Append one rebalance date's full cross-section of predictions.
    Returns False (no-op) if this date is already recorded."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load(PRED_PATH)
    if not existing.empty and (existing["as_of"] == as_of).any():
        return False
    rows = pd.DataFrame({
        "as_of": as_of,
        "ticker": probs.index,
        "prob": probs.values,
        "source": source,
    })
    rows.to_csv(PRED_PATH, mode="a", header=not PRED_PATH.exists(), index=False)
    return True


def update_realized(prices: pd.DataFrame,
                    horizon: int = config.TARGET_HORIZON) -> pd.DataFrame:
    """Score every recorded prediction date whose horizon has completed:
    Spearman IC and top-vs-bottom decile realized spread. Idempotent."""
    preds = _load(PRED_PATH)
    if preds.empty:
        return _load(IC_PATH)
    scored = _load(IC_PATH)
    done = set(scored["as_of"]) if not scored.empty else set()

    returns = prices.pct_change(fill_method=None)
    fwd = forward_return(returns, horizon)
    # a date is scoreable once `horizon` bars exist after it
    scoreable_through = prices.index[-(horizon + 1)] if len(prices) > horizon else None
    if scoreable_through is None:
        return scored

    new_rows = []
    for as_of, grp in preds.groupby("as_of"):
        if as_of in done or as_of > scoreable_through or as_of not in fwd.index:
            continue
        p = grp.set_index("ticker")["prob"]
        r = fwd.loc[as_of].reindex(p.index)
        both = pd.concat({"p": p, "r": r}, axis=1).dropna()
        if len(both) < 50:
            continue
        ic = both["p"].rank().corr(both["r"].rank())  # Spearman
        # method="first" keeps decile buckets populated even under prob ties
        rank = both["p"].rank(pct=True, method="first")
        spread = both.loc[rank > 0.9, "r"].mean() - both.loc[rank <= 0.1, "r"].mean()
        new_rows.append({
            "as_of": as_of, "n": len(both), "ic": ic,
            "decile_spread": spread, "source": grp["source"].iloc[0],
        })
    if new_rows:
        add = pd.DataFrame(new_rows).sort_values("as_of")
        add.to_csv(IC_PATH, mode="a", header=not IC_PATH.exists(), index=False)
        scored = pd.concat([scored, add], ignore_index=True)
    return scored.sort_values("as_of") if not scored.empty else scored


def health_summary(ic_history: pd.DataFrame, data_through,
                   window: int = 26) -> dict:
    """Traffic-light health readout. The point is knowing when NOT to trust
    the model: an edge this size can sit underwater for quarters, but a
    significantly negative trailing IC means stand down."""
    out = {"window": window}

    today = pd.Timestamp.today().normalize()
    age = len(pd.bdate_range(pd.Timestamp(data_through), today)) - 1
    out["data_age_bdays"] = max(age, 0)
    out["data_status"] = "green" if age <= 3 else ("yellow" if age <= 7 else "red")

    if ic_history is None or ic_history.empty or len(ic_history) < 8:
        n = 0 if ic_history is None or ic_history.empty else len(ic_history)
        out.update(model_status="warming", model_detail=f"{n} scored weeks — "
                   "needs 8+ for a live verdict", ic_mean=np.nan, ic_t=np.nan,
                   n_scored=n, spread_bps=np.nan)
        return out

    recent = ic_history.tail(window)
    ic_mean = float(recent["ic"].mean())
    ic_t = float(ic_mean / recent["ic"].std() * np.sqrt(len(recent)))
    spread_bps = float(recent["decile_spread"].mean() * 1e4)
    out.update(ic_mean=ic_mean, ic_t=ic_t, n_scored=len(ic_history),
               spread_bps=spread_bps)

    if ic_t > 1.0:
        out.update(model_status="green",
                   model_detail=f"edge intact — trailing {len(recent)}w IC "
                                f"{ic_mean:+.3f} (t={ic_t:.1f})")
    elif ic_t > -1.0:
        out.update(model_status="yellow",
                   model_detail=f"edge indistinct from zero over the trailing "
                                f"{len(recent)}w (IC {ic_mean:+.3f}, t={ic_t:.1f}) "
                                "— normal for an edge this size, but size down")
    else:
        out.update(model_status="red",
                   model_detail=f"edge INVERTED over the trailing {len(recent)}w "
                                f"(IC {ic_mean:+.3f}, t={ic_t:.1f}) — do not trade "
                                "this book until it recovers")
    return out
