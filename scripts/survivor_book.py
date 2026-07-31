"""Current target book of the cycle-13 survivor: cross-sectional multi-asset
relative value, decile construction with tau=0.25 partial rebalancing — the
config that walk-forward selection actually picked (WF Sharpe 0.852,
full-window 0.711; RESEARCH_NOTES "broad book stays decile", arm-C is
S&P-specific).

Writes reports/dashboard/survivor_book.json for the Vig desk screen:

    python scripts/survivor_book.py
"""
import json

import pandas as pd

from quark import config
from quark.data.loader import compute_returns, load_prices
from quark.ml.xsec import (_decile_weights, partial_rebalance_weights,
                           run_xsec_strategy)
from quark.universe import load_universe


def main() -> None:
    u = load_universe()
    u = u[u["tradable"] & ~u["hindsight_picked"].fillna(False)]
    prices = load_prices(tickers=list(u.index), start="2005-01-01").dropna(how="all")
    volumes = prices.notna().astype(float)
    returns = compute_returns(prices)

    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                            top_frac=0.15,
                            elig_kwargs=dict(min_price=0.0, min_dollar_vol=0.0,
                                             min_history=252))
    preds = res.predictions
    targets = preds.apply(_decile_weights, axis=1, top_frac=0.15)
    held = partial_rebalance_weights(targets, 0.25)

    latest = held.iloc[-1]
    as_of = held.index[-1]
    live = latest[latest.abs() > 0.002].sort_values()
    positions = [
        {"ticker": t, "name": str(u.loc[t, "name"]) if "name" in u.columns else t,
         "asset_class": str(u.loc[t, "asset_class"]),
         "weight": round(float(w), 4)}
        for t, w in live.items()
    ]

    stats = {}
    stats_f = config.REPORTS_DIR / "cycle13_multiasset.csv"
    if stats_f.exists():
        tbl = pd.read_csv(stats_f, index_col=0)
        if "decile_t0.25" in tbl.index:
            s = tbl.loc["decile_t0.25"]
            stats = {k: round(float(s[k]), 4) for k in
                     ("sharpe", "ann_vol", "max_dd", "hit_rate") if k in s}

    out = {"as_of": str(as_of.date()), "n_positions": len(positions),
           "gross": round(float(latest.abs().sum()), 3),
           "stats": stats, "positions": positions}
    dest = config.REPORTS_DIR / "dashboard" / "survivor_book.json"
    dest.write_text(json.dumps(out, indent=1))
    print(f"survivor book as of {as_of.date()}: {len(positions)} positions "
          f"(gross {out['gross']:.2f}) -> {dest}")


if __name__ == "__main__":
    main()
