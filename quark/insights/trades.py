"""Top-trade selection with honest, data-grounded explanations.

The "why" for each trade is the set of cross-sectional feature percentiles
that most distinguish the name today — a readout of the model's inputs, not
a story invented after the fact. Conviction is the model's calibrated
probability, which for this edge is deliberately modest (0.55 is a real
signal here; anything claiming 0.9 would be a bug, not a feature).
"""

import pandas as pd

FEATURE_LABELS = {
    "mom_5": "1-week momentum",
    "mom_21": "1-month momentum",
    "mom_63": "3-month momentum",
    "mom_126": "6-month momentum",
    "mom_252": "12-month momentum",
    "vol_ratio_21_63": "short-term vol regime",
    "vol_ratio_63_252": "medium-term vol regime",
    "rsi_14": "RSI(14)",
    "dist_52w_high": "distance from 52-week high",
}


def _drivers(feature_row: pd.Series, k: int = 3) -> list[str]:
    """The k most extreme cross-sectional percentiles for this name."""
    usable = feature_row[[c for c in feature_row.index if c in FEATURE_LABELS]]
    extreme = usable.abs().sort_values(ascending=False).head(k)
    out = []
    for col in extreme.index:
        pct = (usable[col] + 0.5) * 100  # ranks are centered at 0
        out.append(f"{FEATURE_LABELS[col]} in the {pct:.0f}th percentile of the S&P 500")
    return out


def top_trades(
    xsec: dict,
    headlines: dict[str, list[dict]] | None = None,
    n: int = 3,
    horizon_days: int = 5,
) -> list[dict]:
    """The n highest-conviction trades across both legs, with drivers."""
    headlines = headlines or {}
    table, feats = xsec["table"], xsec["features"]

    # Fixed 2 longs + 1 short. The floating by-|p-0.5| rule was retired
    # 2026-07-07 after the past-trades review showed it overweighting the
    # short tail (-32 bps/call over 156 walk-forward weeks vs +28 for this
    # composition; paired t=+2.06) — consistent with the backtest's
    # long-side-driven edge. See RESEARCH_NOTES.
    candidates = ([(t, "LONG") for t in xsec["longs"][:2]] +
                  [(t, "SHORT") for t in xsec["shorts"][-1:]])

    trades = []
    for ticker, side in candidates[:n]:
        prob = float(table.at[ticker, "prob_outperform"])
        edge = prob - 0.5 if side == "LONG" else 0.5 - prob
        news = headlines.get(ticker, [])
        trades.append(
            {
                "ticker": ticker,
                "side": side,
                "prob": prob,
                "edge_pct": edge * 100,
                "rank_pct": float(table.at[ticker, "rank_pct"] * 100),
                "drivers": _drivers(feats.loc[ticker]),
                "headline": news[0] if news else None,
                "sizing": "equal-weight within the decile of a dollar-neutral "
                          f"book (backtested convention); horizon {horizon_days} "
                          "trading days",
            }
        )
    return trades
