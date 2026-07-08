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
from quark.data.loader import compute_returns
from quark.ml.targets import forward_return

LEDGER_DIR = config.REPORTS_DIR / "ledger"
PRED_PATH = LEDGER_DIR / "predictions.csv"
IC_PATH = LEDGER_DIR / "ic_history.csv"


def _load(path, parse=("as_of",)) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, parse_dates=list(parse))
    if not df.empty and "horizon" not in df.columns:
        df["horizon"] = 5  # rows written before the multi-horizon desk
    return df


def record_predictions(as_of: pd.Timestamp, probs: pd.Series,
                       source: str = "live", horizon: int = 5) -> bool:
    """Append one rebalance date's full cross-section of predictions for one
    horizon. Returns False (no-op) if (date, horizon) is already recorded."""
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load(PRED_PATH)
    if not existing.empty and (
            (existing["as_of"] == as_of) & (existing["horizon"] == horizon)).any():
        return False
    rows = pd.DataFrame({
        "as_of": as_of,
        "ticker": probs.index,
        "prob": probs.values,
        "source": source,
        "horizon": horizon,
    })
    header = not PRED_PATH.exists()
    if not header and "horizon" not in pd.read_csv(PRED_PATH, nrows=0).columns:
        existing.to_csv(PRED_PATH, index=False)  # upgrade file in place
    rows.to_csv(PRED_PATH, mode="a", header=header, index=False)
    return True


def update_realized(prices: pd.DataFrame) -> pd.DataFrame:
    """Score every recorded (date, horizon) whose window has completed:
    Spearman IC and top-vs-bottom decile realized spread. Idempotent."""
    preds = _load(PRED_PATH)
    if preds.empty:
        return _load(IC_PATH)
    scored = _load(IC_PATH)
    done = (set(zip(scored["as_of"], scored["horizon"]))
            if not scored.empty else set())

    returns = compute_returns(prices)
    fwd_cache: dict[int, pd.DataFrame] = {}

    new_rows = []
    for (as_of, horizon), grp in preds.groupby(["as_of", "horizon"]):
        horizon = int(horizon)
        if len(prices) <= horizon:
            continue
        scoreable_through = prices.index[-(horizon + 1)]
        if (as_of, horizon) in done or as_of > scoreable_through:
            continue
        if horizon not in fwd_cache:
            fwd_cache[horizon] = forward_return(returns, horizon)
        fwd = fwd_cache[horizon]
        if as_of not in fwd.index:
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
        # survivorship accounting: predictions we could no longer score
        # (delistings skew toward blowups, which flatters the IC — log it)
        new_rows.append({
            "as_of": as_of, "n": len(both), "ic": ic,
            "decile_spread": spread, "source": grp["source"].iloc[0],
            "horizon": horizon, "n_unscoreable": int(len(p) - len(both)),
        })
    if new_rows:
        add = pd.DataFrame(new_rows).sort_values("as_of")
        if not IC_PATH.exists() or "horizon" in pd.read_csv(IC_PATH, nrows=0).columns:
            add.to_csv(IC_PATH, mode="a", header=not IC_PATH.exists(), index=False)
        else:
            pd.concat([scored, add], ignore_index=True).to_csv(IC_PATH, index=False)
        scored = pd.concat([scored, add], ignore_index=True)
    return scored.sort_values("as_of") if not scored.empty else scored


def health_summary(ic_history: pd.DataFrame, data_through,
                   window: int = 26, horizon: int = 5) -> dict:
    """Traffic-light health readout for one horizon's model. The point is
    knowing when NOT to trust it: an edge this size can sit underwater for
    quarters, but a significantly negative trailing IC means stand down."""
    if ic_history is not None and not ic_history.empty and "horizon" in ic_history.columns:
        ic_history = ic_history[ic_history["horizon"] == horizon]
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
