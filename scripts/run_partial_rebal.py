"""Cycle-1 study: Garleanu-Pedersen-style partial rebalancing of the
flagship weekly cross-sectional book.

PRE-REGISTERED TRIALS (declared before any result was seen; all reported):
    tau in [1.00 (baseline), 0.50, 0.25, 0.15, 0.10, 0.05]

Motivation: reports/deep_research_net_alpha_2026-07-22.md — cost-awareness
at construction time (partial trading toward the target book, which tilts
holdings toward the persistent signal component) is the highest documented
gain-per-effort lever; ex-post band overlays alone are documented to fail
for ML signals. Quark's own hysteresis study (turnover_study.csv) is the
in-house baseline to beat.

Discipline: read the tau *pattern*, not the argmax — with 6 trials the best
single Sharpe is subject to selection, same DSR caveat as turnover_study.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import load_sp500_tickers
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)
from quark.universe import EQUITY_COST_BPS

TAUS = [1.00, 0.50, 0.25, 0.15, 0.10, 0.05]


def main() -> None:
    tickers = load_sp500_tickers()
    prices = load_prices(tickers=tickers, start="2005-01-01")
    volumes = load_prices(tickers=tickers, start="2005-01-01", field="volume")
    report = quality_report(prices)
    prices = clean_panel(prices, report).dropna(how="all")
    volumes = volumes.reindex(prices.index)
    returns = compute_returns(prices)

    print("Training walk-forward model once (h=5, weekly)...")
    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1)
    targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
    oos_start = res.predictions.index[0]

    rows = {}
    for tau in TAUS:
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=7).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
        oos = bt.portfolio.index >= oos_start
        r = bt.portfolio[oos]
        stats = summary_stats(r)
        n_years = oos.sum() / config.ANN_FACTOR
        stats["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
        stats["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
        stats["gross_exposure"] = float(daily[oos].abs().sum(axis=1).mean())
        rows[f"tau_{tau:.2f}"] = stats
        print(f"tau={tau:.2f} done: sharpe={stats.get('sharpe', float('nan')):.3f} "
              f"turnover={stats['ann_turnover']:.1f}x "
              f"drag={stats['cost_drag_ann'] * 1e4:.0f}bps")

    table = pd.DataFrame(rows).T
    config.REPORTS_DIR.mkdir(exist_ok=True)
    table.to_csv(config.REPORTS_DIR / "partial_rebal_study.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 1: partial rebalancing, net of costs (OOS) ===")
        print(table)


if __name__ == "__main__":
    main()
