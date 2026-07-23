"""Cycle 7: SUE-history features + gross profitability (PIT panel).

Motivated by VERIFIED research-2 findings (deep_research_families_2026-07-23):
- Single-quarter PEAD is dead in large caps (independently replicating our
  cycle-3 null) — but elastic-net over 12 QUARTERS of SUE lags nearly
  doubles Sharpe (0.34->0.63), gains strongest in LARGE caps. Multi-quarter
  aggregates are staleness-tolerant, so EDGAR filed-date vintages suffice.
- The best-documented large-cap survivor is GROSS profitability (GP/assets),
  not ROA; fetched via us-gaap GrossProfit (TTM / assets).

PRE-REGISTERED (all reported): features = cycle-4 fundamentals + 6 SUE-
history panels + gp_assets (if GrossProfit coverage permits). Configs:
  weekly h=5 tau {0.10}; monthly h=21 tau {0.50, 0.25};
  blend(weekly 0.10 + monthly 0.25) 50/50.
Baselines (cycles 4-6): weekly tau0.10 0.192; monthly tau0.50 0.211 /
tau0.25 0.273; blend 0.276.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.edgar import (
    _event_panel,
    cik_map,
    compute_sue,
    fetch_concept,
    fundamental_feature_panels,
    sue_history_panels,
)
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


def fetch_grossprofit(tickers, cache_path):
    import time
    try:
        return pd.read_csv(cache_path, parse_dates=["end", "filed"])
    except FileNotFoundError:
        pass
    cmap = cik_map()
    parts = []
    for i, t in enumerate(tickers):
        cik = cmap.get(t.upper().replace("-", "")) or cmap.get(t.upper())
        if cik is None:
            continue
        df = fetch_concept(cik, "GrossProfit", quarterly=True)
        time.sleep(0.11)
        if df is not None and not df.empty:
            df.insert(0, "ticker", t)
            parts.append(df)
        if (i + 1) % 100 == 0:
            print(f"  GrossProfit {i + 1}/{len(tickers)}")
    out = (pd.concat(parts, ignore_index=True)
           if parts else pd.DataFrame(columns=["ticker", "end", "filed", "val"]))
    out.to_csv(cache_path, index=False)
    return out


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
    data_dir = config.REPORTS_DIR.parent / "data"

    fund = pd.read_csv(data_dir / "edgar_fundamentals.csv",
                       parse_dates=["end", "filed"])
    extras = fundamental_feature_panels(fund, prices)

    eps = pd.read_csv(data_dir / "edgar_eps.csv", parse_dates=["end", "filed"])
    sue = compute_sue(eps)
    extras.update(sue_history_panels(sue, prices.index, prices.columns))

    print("Fetching GrossProfit (cached)...")
    gp = fetch_grossprofit(list(prices.columns), data_dir / "edgar_grossprofit.csv")
    if gp["ticker"].nunique() >= 300:
        parts = []
        for t, tg in gp.groupby("ticker"):
            tg = tg.sort_values("end").drop_duplicates("end")
            parts.append(pd.DataFrame(
                {"ticker": t, "filed": tg["filed"],
                 "val": tg["val"].rolling(4).sum()}))
        gp_ttm = _event_panel(
            pd.concat(parts, ignore_index=True).dropna(subset=["val"]),
            prices.index, prices.columns, 300)
        assets_p = _event_panel(
            fund[fund["concept"] == "assets"][["ticker", "filed", "val"]],
            prices.index, prices.columns, 300)
        extras["gp_assets"] = gp_ttm / assets_p.where(assets_p > 0)
        print(f"gp_assets built: {gp['ticker'].nunique()} tickers")
    else:
        print(f"GrossProfit coverage thin ({gp['ticker'].nunique()}), skipped")

    for k in ("sue_mean12", "gp_assets"):
        if k in extras:
            cov = extras[k].notna().mean(axis=1)
            print(f"  {k}: coverage {cov[cov.index >= '2012'].mean():.1%} (2012+)")

    rows = {}
    books = {}
    for name, kw, taus, ffl in [
        ("weekly", dict(horizon=5, rebal_every=1), [0.10], 7),
        ("monthly", dict(horizon=21, rebal_every=4), [0.50, 0.25], 28),
    ]:
        print(f"Training {name} + full feature set...")
        res = run_xsec_strategy(prices, volumes, membership=membership,
                                extra_features=extras, **kw)
        ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
        print(f"  IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
        res.predictions.to_parquet(
            config.REPORTS_DIR / f"preds_{name}_c7_pit.parquet")
        targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
        oos_start = res.predictions.index[0]
        for tau in taus:
            held = partial_rebalance_weights(targets, tau)
            daily = held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)
            books[f"{name}_{tau:.2f}"] = daily
            bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
            key = f"{name}_tau{tau:.2f}"
            rows[key] = stats_row(bt, oos_start,
                                  {"ic_mean": float(res.ic.mean()), "ic_t": ic_t})
            print(f"  {key}: sharpe={rows[key].get('sharpe'):.3f}")

    blend = 0.5 * books["weekly_0.10"] + 0.5 * books["monthly_0.25"]
    bt = run_weights_backtest(blend, returns, cost_bps=EQUITY_COST_BPS)
    rows["blend_c7"] = stats_row(bt, pd.Timestamp("2012-01-06"))
    print(f"blend_c7: sharpe={rows['blend_c7'].get('sharpe'):.3f}")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle7_suehistory.csv")
    with pd.option_context("display.width", 220,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 7: SUE history + gross profitability (PIT) ===")
        print(table)


if __name__ == "__main__":
    main()
