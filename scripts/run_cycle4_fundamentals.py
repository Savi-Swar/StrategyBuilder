"""Cycle 4: the slow fundamental families enter the flagship (PIT panel).

Motivated by VERIFIED findings from deep-research run 2 (2026-07-22/23):
- Gross profitability survives specifically in large caps (26bps/mo, t=1.88,
  Novy-Marx OSoV), incremental to book-to-market, undiminished by size.
- Profitability and value are negatively correlated (-0.57): combining
  roughly doubles Sharpe (large-cap 50/50 Sharpe 0.44 vs 0.27/0.14 alone).
- Novy-Marx rank-combo (profit rank + B/M rank, top/bottom 150 of largest
  500, annual rebalance) earned 0.62%/mo, Sharpe 0.74, ~1/3 turnover/yr.
- McLean-Pontiff: post-publication decay ~58%, WORST in large caps —
  haircut all expectations accordingly.

PRE-REGISTERED (before results; all reported):
  A) ML arm: weekly h=5 PIT + 5 fundamental extras
     (value_bm, profit_roa, asset_growth, net_issuance, accruals),
     taus {1.00, 0.25, 0.10}
  B) Reference arm (no ML): Novy-Marx-style rank combo on our PIT panel —
     rank(value_bm) + rank(profit_roa), long top 30% / short bottom 30%
     of eligible names, ANNUAL rebalance, as a sanity benchmark.
Baselines: cycle-2 PIT weekly no-extras IC +0.0125 (t=2.35),
net Sharpe -0.13 (tau=1.00) / +0.10 (tau=0.25).
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

TAUS = [1.00, 0.25, 0.10]


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
    for k, v in extras.items():
        cov = v.notna().mean(axis=1)
        print(f"  {k}: coverage {cov[cov.index >= '2012'].mean():.1%} (2012+)")

    rows = {}

    # --- Arm B first (cheap): Novy-Marx-style rank combo, annual rebalance
    elig = membership.reindex(prices.index).ffill().fillna(False).astype(bool)
    score = (extras["value_bm"].rank(axis=1, pct=True)
             + extras["profit_roa"].rank(axis=1, pct=True)).where(elig)
    year_ends = prices.index.to_series().resample("YE").last().dropna()
    tgt = {}
    for dt in year_ends:
        row = score.loc[dt].dropna()
        if len(row) < 100:
            continue
        r = row.rank(pct=True)
        w = pd.Series(0.0, index=score.columns)
        long, short = r > 0.7, r <= 0.3
        w[long.index[long]] = 0.5 / long.sum()
        w[short.index[short]] = -0.5 / short.sum()
        tgt[dt] = w
    nm_w = pd.DataFrame(tgt).T.reindex(prices.index).ffill(limit=260).fillna(0.0)
    bt_nm = run_weights_backtest(nm_w, returns, cost_bps=EQUITY_COST_BPS)
    rows["nm_rank_combo_annual"] = stats_row(bt_nm, pd.Timestamp("2012-01-01"))
    print(f"nm_rank_combo: sharpe={rows['nm_rank_combo_annual'].get('sharpe'):.3f}")

    # --- Arm A: ML with fundamental extras
    print("Training weekly h=5 + fundamentals on PIT panel...")
    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                            membership=membership, extra_features=extras)
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)}) "
          f"[baseline +0.0125, t=2.35]")
    targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
    oos_start = res.predictions.index[0]
    for tau in TAUS:
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=7).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
        rows[f"fund_tau{tau:.2f}"] = stats_row(
            bt, oos_start, {"ic_mean": float(res.ic.mean()), "ic_t": ic_t})
        print(f"tau={tau:.2f}: sharpe={rows[f'fund_tau{tau:.2f}'].get('sharpe'):.3f}")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle4_fundamentals.csv")
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 4: PIT + fundamental families, net of costs ===")
        print(table)


if __name__ == "__main__":
    main()
