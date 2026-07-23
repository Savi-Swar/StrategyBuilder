"""Cycle 5: two pre-registered follow-ups to cycle 4's result.

Cycle 4 found: fundamentals lift net Sharpe at every tau and the tau-curve
was still RISING at the slowest tested point (0.10 -> 0.19). Two questions:

  A) Where does the tau-curve peak now? taus {0.15, 0.05, 0.03} on the
     weekly h=5 + fundamentals model (cycle 2 showed 0.05 collapses for the
     price-only signal; if the composite is more persistent, slower should
     now hold up — this is a direct test of the persistence interpretation).
  B) Do slow features revive the monthly horizon? h=21, rebal_every=4 +
     fundamentals, taus {1.00, 0.50}. Baseline: price-only monthly PIT IC
     was EXACTLY zero (cycle 2) — any positive IC here is attributable to
     the fundamental families.

PRE-REGISTERED: the five configs above, all reported. Predictions saved to
reports/preds_* parquet for reuse (no more retraining to extend tau grids).
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.edgar import fundamental_feature_panels
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)
from quark.universe import EQUITY_COST_BPS


def stats_row(bt, oos_start, extra=None):
    oos = bt.portfolio.index >= oos_start
    s = summary_stats(bt.portfolio[oos])
    n_years = oos.sum() / config.ANN_FACTOR
    s["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
    s["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
    if extra:
        s.update(extra)
    return s


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
    fund = pd.read_csv(config.REPORTS_DIR.parent / "data" / "edgar_fundamentals.csv",
                       parse_dates=["end", "filed"])
    extras = fundamental_feature_panels(fund, prices)

    rows = {}
    configs = [
        ("weekly", dict(horizon=5, rebal_every=1), [0.15, 0.05, 0.03], 7),
        ("monthly", dict(horizon=21, rebal_every=4), [1.00, 0.50], 28),
    ]
    for name, kw, taus, ffl in configs:
        print(f"Training {name} + fundamentals on PIT panel...")
        res = run_xsec_strategy(prices, volumes, membership=membership,
                                extra_features=extras, **kw)
        ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
        print(f"  IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
        res.predictions.to_parquet(
            config.REPORTS_DIR / f"preds_{name}_fund_pit.parquet")
        targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
        oos_start = res.predictions.index[0]
        for tau in taus:
            held = partial_rebalance_weights(targets, tau)
            daily = held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)
            bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
            key = f"{name}_tau{tau:.2f}"
            rows[key] = stats_row(bt, oos_start,
                                  {"ic_mean": float(res.ic.mean()), "ic_t": ic_t})
            print(f"  {key}: sharpe={rows[key].get('sharpe'):.3f}")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle5_slowprobe.csv")
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 5: slow-tau probe + monthly revival test ===")
        print(table)


if __name__ == "__main__":
    main()
