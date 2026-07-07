"""Past-trades review: reconstruct the top-3 calls Vig would have made at
every rebalance over the past year (from the ledger's genuine out-of-sample
predictions), grade each against realized returns, and diagnose patterns.

Grading is relative-first because that is the model's actual claim: it
predicts winners VS the cross-section, not absolute direction. A LONG wins
if it beat the S&P median over the 5 days; a SHORT wins if it lagged it.
Absolute P&L is shown too, honestly labeled.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.insights.ledger import _load, PRED_PATH
from quark.ml.targets import forward_return

TOP_FRAC = 0.10


def _top3_for_week(probs: pd.Series) -> list[tuple[str, str, float]]:
    """Same selection rule as the live top_trades: fixed 2 longs + 1 short
    (adopted 2026-07-07 after the review showed the floating-side rule
    overweighting the alpha-free short tail — see RESEARCH_NOTES)."""
    longs = probs.nlargest(2)
    short = probs.nsmallest(1)
    return ([(t, "LONG", p) for t, p in longs.items()] +
            [(t, "SHORT", p) for t, p in short.items()])


def _grade_dates(preds: pd.DataFrame, fwd: pd.DataFrame,
                 dates, scoreable_through) -> pd.DataFrame:
    rows = []
    for as_of in dates:
        if as_of > scoreable_through or as_of not in fwd.index:
            continue
        week = preds[preds["as_of"] == as_of].set_index("ticker")["prob"]
        realized = fwd.loc[as_of]
        median = realized.reindex(week.index).median()
        for ticker, side, prob in _top3_for_week(week):
            r = realized.get(ticker, np.nan)
            if pd.isna(r):
                continue
            rel = (r - median) if side == "LONG" else (median - r)
            pnl = r if side == "LONG" else -r
            rows.append({
                "as_of": as_of, "ticker": ticker, "side": side,
                "prob": prob, "conviction": abs(prob - 0.5),
                "ret_5d": r, "rel_5d": rel, "pnl_5d": pnl,
                "win_rel": rel > 0, "win_abs": pnl > 0,
            })
    return pd.DataFrame(rows)


def build_review(prices: pd.DataFrame, weeks: int = 52,
                 horizon: int = config.TARGET_HORIZON) -> dict:
    preds = _load(PRED_PATH)
    if preds.empty:
        return {"trades": pd.DataFrame(), "summary": {}, "lessons": []}

    returns = prices.pct_change(fill_method=None)
    fwd = forward_return(returns, horizon)
    scoreable_through = prices.index[-(horizon + 1)]

    all_dates = sorted(preds["as_of"].unique())
    trades = _grade_dates(preds, fwd, all_dates[-weeks:], scoreable_through)
    if trades.empty:
        return {"trades": trades, "summary": {}, "lessons": []}

    # Full-history context: a bad display window must be judged against the
    # whole record, or the review overfits to the latest regime.
    full = _grade_dates(preds, fwd, all_dates, scoreable_through)

    weekly_rel = trades.groupby("as_of")["rel_5d"].mean()
    summary = {
        "n_trades": len(trades),
        "n_weeks": trades["as_of"].nunique(),
        "hit_rel": float(trades["win_rel"].mean()),
        "hit_abs": float(trades["win_abs"].mean()),
        "avg_rel_bps": float(trades["rel_5d"].mean() * 1e4),
        "avg_pnl_bps": float(trades["pnl_5d"].mean() * 1e4),
        "cum_rel": [round(float(v), 5) for v in weekly_rel.cumsum()],
        "by_side": {
            s: {"n": int(g.shape[0]), "hit_rel": float(g["win_rel"].mean()),
                "avg_rel_bps": float(g["rel_5d"].mean() * 1e4)}
            for s, g in trades.groupby("side")
        },
        "by_conviction": _conviction_buckets(trades),
        "max_losing_streak": _max_streak(weekly_rel < 0),
        "full_history": {
            "n": int(len(full)),
            "weeks": int(full["as_of"].nunique()),
            "hit_rel": float(full["win_rel"].mean()),
            "avg_rel_bps": float(full["rel_5d"].mean() * 1e4),
        },
    }
    return {"trades": trades, "summary": summary,
            "lessons": _lessons(trades, summary)}


def _conviction_buckets(trades: pd.DataFrame) -> list[dict]:
    labeled = trades.assign(
        bucket=pd.qcut(trades["conviction"], 3,
                       labels=["low", "mid", "high"], duplicates="drop"))
    return [
        {"bucket": str(b), "n": int(g.shape[0]),
         "hit_rel": float(g["win_rel"].mean()),
         "avg_rel_bps": float(g["rel_5d"].mean() * 1e4)}
        for b, g in labeled.groupby("bucket", observed=True)
    ]


def _max_streak(losses: pd.Series) -> int:
    streak = best = 0
    for x in losses:
        streak = streak + 1 if x else 0
        best = max(best, streak)
    return int(best)


def _lessons(trades: pd.DataFrame, s: dict) -> list[str]:
    """Rule-based self-diagnosis — computed from the record, not vibes."""
    out = []
    n, hit = s["n_trades"], s["hit_rel"]
    se = np.sqrt(0.25 / n)
    t = (hit - 0.5) / se
    if t > 1.5:
        out.append(f"Relative hit rate {hit:.0%} over {n} calls (t≈{t:.1f} vs "
                   "coin-flip) — the top-3 selection carries real signal.")
    elif t < -1.5:
        out.append(f"Relative hit rate {hit:.0%} over {n} calls is "
                   f"significantly BELOW coin-flip in this window (t≈{t:.1f}) "
                   "— the extreme-conviction tails have been anti-predictive "
                   "recently, even where the full decile book earns its spread.")
    else:
        out.append(f"Relative hit rate {hit:.0%} over {n} calls is not "
                   f"distinguishable from 50/50 (t≈{t:.1f}) — judge the "
                   "process, not short-run outcomes.")

    fh = s.get("full_history")
    if fh and fh["weeks"] > s["n_weeks"] + 12:
        drift = s["avg_rel_bps"] - fh["avg_rel_bps"]
        verdict = ("a drawdown inside a noisy-positive record — watch it, "
                   "don't flinch; changing the rule on one bad year is how "
                   "edges get overfitted away"
                   if fh["avg_rel_bps"] > 0 > s["avg_rel_bps"] else
                   "consistent with the longer record")
        out.append(f"Context: over the full {fh['weeks']}-week record the same "
                   f"rule averages {fh['avg_rel_bps']:+.0f} bps/call (hit "
                   f"{fh['hit_rel']:.0%}); this window runs {drift:+.0f} bps "
                   f"vs that baseline — {verdict}. Four alternative selection "
                   "rules were tested on the full record (2026-07, see "
                   "RESEARCH_NOTES): none separable from noise, none adopted.")

    bs = s["by_side"]
    if "LONG" in bs and "SHORT" in bs:
        gap = bs["LONG"]["hit_rel"] - bs["SHORT"]["hit_rel"]
        if gap > 0.05:
            out.append(f"Longs hit {bs['LONG']['hit_rel']:.0%} vs shorts "
                       f"{bs['SHORT']['hit_rel']:.0%} — matches the backtest's "
                       "long-side-driven edge. Improvement candidate: tilt "
                       "long (e.g. 2 longs + 1 short is already the natural "
                       "output; consider grading shorts as hedges, not alpha).")
        elif gap < -0.05:
            out.append(f"Shorts ({bs['SHORT']['hit_rel']:.0%}) beat longs "
                       f"({bs['LONG']['hit_rel']:.0%}) in this window — "
                       "contrary to the backtest; likely regime noise, watch it.")

    bc = {b["bucket"]: b for b in s["by_conviction"]}
    if "high" in bc and "low" in bc:
        if bc["high"]["hit_rel"] > bc["low"]["hit_rel"] + 0.03:
            out.append("Higher-conviction calls hit more often — the "
                       "probability is informative beyond the cut, so "
                       "conviction-weighted sizing is justified.")
        else:
            out.append("High-conviction calls do NOT hit more often than "
                       "low-conviction ones in this window — treat the "
                       "probability as a ranking device, size picks equally.")

    out.append(f"Longest weekly losing streak: {s['max_losing_streak']} weeks. "
               "An edge this size guarantees streaks like this — the failure "
               "mode to avoid is abandoning the process inside one.")
    if s["hit_abs"] < s["hit_rel"]:
        out.append(f"Absolute hit rate ({s['hit_abs']:.0%}) trails relative "
                   f"({s['hit_rel']:.0%}): the model picks relative winners; "
                   "in down tapes even good longs lose money. Hedge or accept "
                   "market beta consciously.")
    return out


def llm_self_review(summary: dict, lessons: list[str]) -> str | None:
    """Optional: Vig grades its own year. Same graceful-degradation contract
    as the commentary."""
    try:
        import anthropic
    except ImportError:
        return None
    import json
    prompt = (
        "You are Vig, reviewing your own last year of top-3 weekly calls. "
        "Below are your graded results and rule-based diagnostics. Write an "
        "honest self-review (150-250 words): what the record supports, what "
        "is probably noise given the sample size, and AT MOST two concrete "
        "process improvements that do not amount to overfitting the past "
        "year. No self-congratulation, no self-flagellation — calibration.\n\n"
        f"RESULTS: {json.dumps({k: v for k, v in summary.items() if k != 'cum_rel'})}\n"
        f"DIAGNOSTICS: {json.dumps(lessons)}"
    )
    try:
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model="claude-opus-4-8", max_tokens=4000,
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
        )
        if resp.stop_reason == "refusal":
            return None
        return next((b.text for b in resp.content if b.type == "text"), None)
    except Exception:  # noqa: BLE001 — optional layer, never fatal
        return None
