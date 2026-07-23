"""Cycle 9: walk-forward CONFIG selection — the honesty gate.

Every tau/blend number so far was selected looking at the full OOS window.
This study removes that: for each year Y (2015-2026), the config is chosen
by net Sharpe on 2012..Y-1 ONLY, then applied to year Y; the chained yearly
OOS returns give the honest headline number. Model predictions were always
walk-forward; this closes the last selection leak.

Candidate set (fixed, the grids actually run in cycles 1-6):
  weekly taus {1.00, 0.50, 0.25, 0.15, 0.10, 0.05}
  monthly taus {1.00, 0.50, 0.25}
  blends: 50/50 of every (weekly tau, monthly tau) pair
Uses cached cycle-5 predictions (fund feature set, PIT panel). Reports the
chained walk-forward Sharpe, the per-year chosen config, and the in-sample-
selected 0.276 for comparison. No new trials on the champion — this is a
measurement protocol, not a search.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.ml.xsec import _decile_weights, partial_rebalance_weights
from quark.universe import EQUITY_COST_BPS

W_TAUS = [1.00, 0.50, 0.25, 0.15, 0.10, 0.05]
M_TAUS = [1.00, 0.50, 0.25]


def main() -> None:
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    tickers = sorted(pit["ticker"].unique())
    prices = load_prices(tickers=tickers, start="2005-01-01")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    returns = compute_returns(prices)

    pw = pd.read_parquet(config.REPORTS_DIR / "preds_weekly_fund_pit.parquet")
    pm = pd.read_parquet(config.REPORTS_DIR / "preds_monthly_fund_pit.parquet")

    def net_stream(preds, tau, ffl):
        targets = preds.apply(_decile_weights, axis=1, top_frac=0.10)
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)
        return run_weights_backtest(daily, returns,
                                    cost_bps=EQUITY_COST_BPS).portfolio

    print("Building candidate return streams...")
    streams = {}
    for t in W_TAUS:
        streams[f"w{t:.2f}"] = net_stream(pw, t, 7)
    for t in M_TAUS:
        streams[f"m{t:.2f}"] = net_stream(pm, t, 28)
    for wt in W_TAUS:
        for mt in M_TAUS:
            streams[f"b_w{wt:.2f}_m{mt:.2f}"] = (
                0.5 * streams[f"w{wt:.2f}"] + 0.5 * streams[f"m{mt:.2f}"])
    print(f"{len(streams)} candidate configs")

    start = pd.Timestamp("2012-01-06")
    chained, chosen = [], {}
    for year in range(2015, 2027):
        tr_end = pd.Timestamp(f"{year - 1}-12-31")
        te_end = pd.Timestamp(f"{year}-12-31")
        best, best_sh = None, -np.inf
        for name, s in streams.items():
            tr = s[(s.index >= start) & (s.index <= tr_end)]
            if tr.std() > 0:
                sh = tr.mean() / tr.std() * np.sqrt(config.ANN_FACTOR)
                if sh > best_sh:
                    best, best_sh = name, sh
        te = streams[best][(streams[best].index > tr_end)
                           & (streams[best].index <= te_end)]
        chained.append(te)
        chosen[year] = (best, round(best_sh, 3),
                        round(float(te.mean() / te.std() * np.sqrt(config.ANN_FACTOR))
                              if te.std() > 0 else np.nan, 3))
        print(f"{year}: chose {best} (trailing sharpe {best_sh:.2f}) "
              f"-> realized {chosen[year][2]}")

    wf = pd.concat(chained).sort_index()
    s = summary_stats(wf)
    print("\n=== Cycle 9: walk-forward-selected performance 2015-2026 ===")
    for k in ("cagr", "ann_vol", "sharpe", "max_dd", "skew"):
        print(f"  {k}: {s.get(k):.4f}")
    # Comparison: the in-sample-selected champion measured on the same window
    champ = streams["b_w0.10_m0.25"]
    ch = champ[(champ.index > pd.Timestamp('2014-12-31'))]
    print(f"  [comparison] in-sample champion blend, same window: "
          f"sharpe {ch.mean() / ch.std() * np.sqrt(config.ANN_FACTOR):.4f}")

    pd.DataFrame(chosen, index=["config", "trail_sharpe", "realized_sharpe"]).T\
        .to_csv(config.REPORTS_DIR / "cycle9_walkforward.csv")
    wf.to_csv(config.REPORTS_DIR / "cycle9_wf_returns.csv")


if __name__ == "__main__":
    main()
