"""Cycle 3: first non-price information enters the flagship — EDGAR SUE/PEAD.

Adds two PIT-correct earnings features (quark/data/edgar.py) to the weekly
h=5 model on the best-effort PIT panel:
    sue_recent — last announced Bernard-Thomas SUE, live 75 trading days
    ann_age    — trading days since announcement / 75

PRE-REGISTERED (declared before results seen; all reported):
    config: weekly h=5, PIT membership, taus {1.00, 0.25}
Baselines to beat (cycle2_pit_partial.csv, same panel/config, no earnings):
    IC +0.0125 (t=2.35); net Sharpe -0.13 (tau=1.00), +0.10 (tau=0.25)

Data: SEC XBRL companyconcept, quarterly diluted (fallback basic) EPS,
first-filing vintages, cached to data/edgar_eps.csv (resumable).
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.edgar import (
    compute_sue,
    earnings_feature_panels,
    fetch_eps_panel,
)
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)
from quark.universe import EQUITY_COST_BPS

TAUS = [1.00, 0.25]


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

    cache = config.REPORTS_DIR.parent / "data" / "edgar_eps.csv"
    cache.parent.mkdir(exist_ok=True)
    print("Fetching EDGAR quarterly EPS (cached/resumable)...")
    eps = fetch_eps_panel(list(prices.columns), cache)
    sue = compute_sue(eps)
    print(f"SUE: {sue['ticker'].nunique()} tickers, {len(sue)} announcements, "
          f"{sue['filed'].min():%Y-%m} to {sue['filed'].max():%Y-%m}")
    extras = earnings_feature_panels(sue, prices.index, prices.columns)
    cov = extras["sue_recent"].notna().mean(axis=1)
    print(f"sue_recent coverage (mean fraction of names live): "
          f"{cov[cov.index >= '2012'].mean():.2%} (2012+)")

    print("Training weekly h=5 with earnings features on PIT panel...")
    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                            membership=membership, extra_features=extras)
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})  "
          f"[baseline +0.0125, t=2.35]")

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
        stats["ic_mean"], stats["ic_t"] = float(res.ic.mean()), ic_t
        rows[f"earn_tau{tau:.2f}"] = stats
        print(f"tau={tau:.2f}: net sharpe={stats.get('sharpe', float('nan')):.3f} "
              f"turnover={stats['ann_turnover']:.1f}x")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle3_earnings.csv")
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 3: PIT + earnings features, net of costs ===")
        print(table)


if __name__ == "__main__":
    main()
