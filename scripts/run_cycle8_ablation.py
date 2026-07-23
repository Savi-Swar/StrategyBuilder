"""Cycle 8: one-variable ablation of cycle 7's negative result.

Monthly h=21 config (fast, and where cycle-7 damage concentrated):
  A) fundamentals + SUE-history block (no gp_assets)
  B) fundamentals + gp_assets (no SUE block)
  C) fundamentals only (cycle-5 reproduction / control)
Recovery bar (pre-registered): monthly IC >= +0.0120 (cycle-5 level).
Tau fixed at 0.25 (standing recipe) — one number per arm, no tau search.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.edgar import (
    _event_panel,
    compute_sue,
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
    base = fundamental_feature_panels(fund, prices)

    eps = pd.read_csv(data_dir / "edgar_eps.csv", parse_dates=["end", "filed"])
    sue_block = sue_history_panels(compute_sue(eps), prices.index, prices.columns)

    gp = pd.read_csv(data_dir / "edgar_grossprofit.csv",
                     parse_dates=["end", "filed"])
    parts = []
    for t, tg in gp.groupby("ticker"):
        tg = tg.sort_values("end").drop_duplicates("end")
        parts.append(pd.DataFrame({"ticker": t, "filed": tg["filed"],
                                   "val": tg["val"].rolling(4).sum()}))
    gp_ttm = _event_panel(pd.concat(parts, ignore_index=True).dropna(subset=["val"]),
                          prices.index, prices.columns, 300)
    assets_p = _event_panel(fund[fund["concept"] == "assets"][["ticker", "filed", "val"]],
                            prices.index, prices.columns, 300)
    gp_assets = gp_ttm / assets_p.where(assets_p > 0)

    arms = {
        "A_fund_plus_sue": {**base, **sue_block},
        "B_fund_plus_gp": {**base, "gp_assets": gp_assets},
        "C_fund_only": dict(base),
    }
    rows = {}
    for name, extras in arms.items():
        print(f"Training monthly arm {name} ({len(extras)} extra features)...")
        res = run_xsec_strategy(prices, volumes, horizon=21, rebal_every=4,
                                membership=membership, extra_features=extras)
        ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
        targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
        held = partial_rebalance_weights(targets, 0.25)
        daily = held.reindex(prices.index).ffill(limit=28).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
        oos = bt.portfolio.index >= res.predictions.index[0]
        s = summary_stats(bt.portfolio[oos])
        s["ic_mean"], s["ic_t"] = float(res.ic.mean()), ic_t
        rows[name] = s
        print(f"  IC {res.ic.mean():+.4f} (t={ic_t:.2f}) "
              f"net sharpe {s.get('sharpe'):.3f}")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle8_ablation.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 8: monthly ablation (tau=0.25 fixed) ===")
        print(table)


if __name__ == "__main__":
    main()
