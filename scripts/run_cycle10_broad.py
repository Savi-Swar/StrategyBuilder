"""Cycle 10a: the pond change — same price-only model, 5,594-name universe.

ONE variable vs the S&P PIT baseline (price-only weekly: -0.13 full rebal /
+0.10 tau=0.25): the universe. Verified thesis: published alpha decays most
in large caps; mid/small caps retain more. Tiered realistic costs by
liquidity. Fundamentals join in cycle 10b (broad EDGAR fetch running
separately) — one lever at a time, cycle-7's lesson.

PRE-REGISTERED: weekly h=5, decile L/S, eligibility: price>$5, 63d median
dollar vol > $5M, 252d history (causal, PIT-safe by construction);
costs: 5bps if name's trailing median $vol > $50M, 10bps if > $10M,
else 20bps (assigned causally-ish via full-sample median — documented
approximation); taus {1.00, 0.25, 0.10}.
HONESTY: current-listing panel — upper bound until delisting audit.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)

TAUS = [1.00, 0.25, 0.10]


def main() -> None:
    data_dir = config.REPORTS_DIR.parent / "data"
    prices = pd.read_parquet(data_dir / "broad_prices.parquet")
    dollar_vol = pd.read_parquet(data_dir / "broad_volumes.parquet")
    prices.index = pd.to_datetime(prices.index)
    prices = prices.dropna(how="all")
    dollar_vol = dollar_vol.reindex(prices.index)
    volumes = dollar_vol / prices
    returns = compute_returns(prices)
    print(f"Panel: {prices.shape[1]} names x {prices.shape[0]} days")

    med_dv = dollar_vol.median()
    cost_bps = pd.Series(
        np.where(med_dv > 5e7, 5.0, np.where(med_dv > 1e7, 10.0, 20.0)),
        index=prices.columns)
    print("cost tiers:", (cost_bps.value_counts().to_dict()))

    res = run_xsec_strategy(
        prices, volumes, horizon=5, rebal_every=1,
        elig_kwargs=dict(min_price=5.0, min_dollar_vol=5e6, min_history=252),
    )
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)}) "
          f"names/wk {res.predictions.notna().sum(axis=1).median():.0f}")
    res.predictions.to_parquet(config.REPORTS_DIR / "preds_broad10a.parquet")

    targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
    oos_start = res.predictions.index[0]
    rows = {}
    for tau in TAUS:
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=7).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=cost_bps)
        oos = bt.portfolio.index >= oos_start
        s = summary_stats(bt.portfolio[oos])
        n_years = oos.sum() / config.ANN_FACTOR
        s["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
        s["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
        s["ic_mean"], s["ic_t"] = float(res.ic.mean()), ic_t
        rows[f"tau{tau:.2f}"] = s
        print(f"tau={tau:.2f}: net sharpe={s.get('sharpe'):.3f} "
              f"drag={s['cost_drag_ann']*1e4:.0f}bps")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle10a_broad.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 10a: broad universe, price-only (UPPER BOUND) ===")
        print(table)


if __name__ == "__main__":
    main()
