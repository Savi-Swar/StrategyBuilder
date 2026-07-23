"""Cycle 6: blend the two live books (weekly tau=0.10 + monthly tau=0.50).

Both books carry partially independent information (weekly: persistent
price component; monthly: fundamentals-driven horizon). If their return
streams are imperfectly correlated, a 50/50 capital split earns a
diversification Sharpe bump at zero new information cost.

PRE-REGISTERED: three trials, all reported.
  1) blend_50_50: half capital in each book
  2) monthly_tau0.25: extends the monthly tau grid one step (was rising)
  3) blend_50_50_slow: weekly tau=0.10 + monthly tau=0.25
Also reported (diagnostics, not trials): correlation of the two book
return streams. Uses cached predictions — no retraining.
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


def book(preds, prices, tau, ffl):
    targets = preds.apply(_decile_weights, axis=1, top_frac=0.10)
    held = partial_rebalance_weights(targets, tau)
    return held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)


def stats_row(bt, oos_start):
    oos = bt.portfolio.index >= oos_start
    s = summary_stats(bt.portfolio[oos])
    n_years = oos.sum() / config.ANN_FACTOR
    s["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
    s["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
    return s


def main() -> None:
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    tickers = sorted(pit["ticker"].unique())
    prices = load_prices(tickers=tickers, start="2005-01-01")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    returns = compute_returns(prices)

    pw = pd.read_parquet(config.REPORTS_DIR / "preds_weekly_fund_pit.parquet")
    pm = pd.read_parquet(config.REPORTS_DIR / "preds_monthly_fund_pit.parquet")
    oos_start = max(pw.index[0], pm.index[0])

    wk = book(pw, prices, 0.10, 7)
    mo50 = book(pm, prices, 0.50, 28)
    mo25 = book(pm, prices, 0.25, 28)

    # Diagnostics: correlation of the two standalone net return streams
    bt_wk = run_weights_backtest(wk, returns, cost_bps=EQUITY_COST_BPS)
    bt_mo = run_weights_backtest(mo50, returns, cost_bps=EQUITY_COST_BPS)
    m = bt_wk.portfolio.index >= oos_start
    corr = float(bt_wk.portfolio[m].corr(bt_mo.portfolio[m]))
    print(f"book correlation (weekly vs monthly, OOS): {corr:+.3f}")

    rows = {}
    for name, w in [
        ("blend_50_50", 0.5 * wk + 0.5 * mo50),
        ("monthly_tau0.25", mo25),
        ("blend_50_50_slow", 0.5 * wk + 0.5 * mo25),
    ]:
        bt = run_weights_backtest(w, returns, cost_bps=EQUITY_COST_BPS)
        rows[name] = stats_row(bt, oos_start)
        print(f"{name}: sharpe={rows[name].get('sharpe'):.3f} "
              f"turnover={rows[name]['ann_turnover']:.1f}x")

    table = pd.DataFrame(rows).T
    table["book_corr"] = corr
    table.to_csv(config.REPORTS_DIR / "cycle6_blend.csv")
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 6: book blending, net of costs (PIT) ===")
        print(table)


if __name__ == "__main__":
    main()
