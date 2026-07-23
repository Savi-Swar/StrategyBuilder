"""Crypto cycle 1: cross-sectional ML long-short on the Binance panel.

Same engine, new ocean. PRE-REGISTERED (before any result; all reported):
  weekly cadence (h=7 calendar days), top/bottom decile, dollar-neutral
  eligibility: 63d median dollar volume > $10M, history >= 90d, no price floor
  costs: 10 bps on turnover (Binance taker 10bps; spreads extra — stress later)
  taus {1.00, 0.25, 0.10}
HONESTY: current-listing panel (delisted coins absent) — every number here
is an UPPER BOUND until the CoinGecko dead-coin audit measures the bias.
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

COST_BPS = 10.0
TAUS = [1.00, 0.25, 0.10]


def main() -> None:
    data_dir = config.REPORTS_DIR.parent / "data"
    prices = pd.read_csv(data_dir / "crypto_prices.csv",
                         index_col=0, parse_dates=True)
    dollar_vol = pd.read_csv(data_dir / "crypto_volumes.csv",
                             index_col=0, parse_dates=True)
    volumes = dollar_vol / prices          # engine computes $vol = p*v
    returns = compute_returns(prices)
    print(f"Panel: {prices.shape[1]} coins x {prices.shape[0]} days")

    res = run_xsec_strategy(
        prices, volumes, horizon=7, rebal_every=1,
        elig_kwargs=dict(min_price=0.0, min_dollar_vol=1e7, min_history=90),
    )
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
    print(f"names/week median: {res.predictions.notna().sum(axis=1).median():.0f}")
    res.predictions.to_parquet(config.REPORTS_DIR / "preds_crypto_pit.parquet")

    targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
    oos_start = res.predictions.index[0]
    rows = {}
    for tau in TAUS:
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=10).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=COST_BPS)
        oos = bt.portfolio.index >= oos_start
        s = summary_stats(bt.portfolio[oos])
        n_years = oos.sum() / 365.0
        s["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
        s["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
        s["ic_mean"], s["ic_t"] = float(res.ic.mean()), ic_t
        rows[f"tau{tau:.2f}"] = s
        print(f"tau={tau:.2f}: net sharpe={s.get('sharpe'):.3f} "
              f"turnover={s['ann_turnover']:.1f}x drag={s['cost_drag_ann']*1e4:.0f}bps")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "crypto_cycle1.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Crypto cycle 1: xsec ML L/S, net of costs (UPPER BOUND) ===")
        print(table)


if __name__ == "__main__":
    main()
