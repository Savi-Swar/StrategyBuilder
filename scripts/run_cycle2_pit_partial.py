"""Cycle 2: the two surviving levers, evaluated on the PIT panel directly.

Cycle-1 result (partial_rebal_study.csv, current-members panel): partial
rebalancing lifts weekly net Sharpe 0.06 -> 0.50 monotonically in tau.
Survivorship carried the baseline economics (pit_study.csv), so nothing is
believed until it survives point-in-time membership. This study therefore
runs BOTH remaining levers on the best-effort PIT panel:

  A) weekly h=5 predictions + partial trading, tau in [1.00, 0.25, 0.10, 0.05]
  B) monthly h=21 predictions (rebal_every=4) + partial trading,
     tau in [1.00, 0.50, 0.25]

PRE-REGISTERED: the two configs and seven tau values above were declared
before any PIT result was seen; all are reported. Read patterns, not argmax
(same DSR discipline as turnover_study). PIT panel remains optimistic
(45% delisted recovery, zero-return delisting convention) — treat results
as an upper bound tightened, not truth.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)
from quark.universe import EQUITY_COST_BPS

CONFIGS = [
    {"name": "weekly_h5", "horizon": 5, "rebal_every": 1,
     "taus": [1.00, 0.25, 0.10, 0.05], "ffill_limit": 7},
    {"name": "monthly_h21", "horizon": 21, "rebal_every": 4,
     "taus": [1.00, 0.50, 0.25], "ffill_limit": 28},
]


def main() -> None:
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    mask = (pit.assign(v=1.0)
            .pivot(index="month_end", columns="ticker", values="v")
            .notna())
    prices = load_prices(tickers=sorted(mask.columns), start="2005-01-01")
    volumes = load_prices(tickers=sorted(mask.columns), start="2005-01-01",
                          field="volume")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    volumes = volumes.reindex(prices.index)
    returns = compute_returns(prices)
    membership = mask[prices.columns]
    print(f"PIT panel: {prices.shape[1]} names")

    rows = {}
    for cfg in CONFIGS:
        print(f"Training {cfg['name']} on PIT panel...")
        res = run_xsec_strategy(prices, volumes, horizon=cfg["horizon"],
                                rebal_every=cfg["rebal_every"],
                                membership=membership)
        ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
        print(f"  IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
        targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
        oos_start = res.predictions.index[0]

        for tau in cfg["taus"]:
            held = partial_rebalance_weights(targets, tau)
            daily = (held.reindex(prices.index)
                     .ffill(limit=cfg["ffill_limit"]).fillna(0.0))
            bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
            oos = bt.portfolio.index >= oos_start
            r = bt.portfolio[oos]
            stats = summary_stats(r)
            n_years = oos.sum() / config.ANN_FACTOR
            stats["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
            stats["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
            stats["gross_exposure"] = float(daily[oos].abs().sum(axis=1).mean())
            stats["ic_mean"] = float(res.ic.mean())
            stats["ic_t"] = ic_t
            key = f"{cfg['name']}_tau{tau:.2f}"
            rows[key] = stats
            print(f"  {key}: sharpe={stats.get('sharpe', float('nan')):.3f} "
                  f"turnover={stats['ann_turnover']:.1f}x "
                  f"drag={stats['cost_drag_ann'] * 1e4:.0f}bps")

    table = pd.DataFrame(rows).T
    out = config.REPORTS_DIR / "cycle2_pit_partial.csv"
    table.to_csv(out)
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 2: PIT panel, partial rebalancing, net of costs ===")
        print(table)


if __name__ == "__main__":
    main()
