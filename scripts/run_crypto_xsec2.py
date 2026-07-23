"""Crypto cycle 2: rerun with evidence-based data-quality layer.

Cycle-1 postmortem (crypto_cycle1.csv): ann_vol ~300 was a DATA ARTIFACT —
Binance reused the LUNA ticker after the Terra collapse, and gap-bridging
returns (correct for equity holidays) glued old-LUNA's death to LUNA2's
listing: +17,739,900% in one untradeable "day". Real crypto tails (DOGE
+392% Jan-2021) must be KEPT — the rule targets ticker-reuse/halts only:

  CLEANING RULE (pre-registered from the diagnostic, not tuned on results):
  1) In a 24/7 market, any gap > 3 days = halt/delist/redenomination.
     Break the series at such gaps; keep only the LATEST contiguous segment.
  2) Drop stablecoins/fiat proxies (no cross-sectional signal, pollute ranks).

Same pre-registered configs as cycle 1: h=7 weekly, decile L/S, $10M
liquidity screen, 10bps costs, taus {1.00, 0.25, 0.10}. Still a
current-listing panel: UPPER BOUND, say it every time.
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
STABLES = {"USDC", "TUSD", "BUSD", "DAI", "FDUSD", "USDP", "AEUR", "EUR",
           "EURI", "USDE", "USD1", "XUSD", "PAXG", "USTC"}


def clean_crypto(prices: pd.DataFrame, max_gap_days: int = 3) -> pd.DataFrame:
    out = prices.drop(columns=[c for c in prices.columns if c in STABLES])
    cleaned = {}
    for c in out.columns:
        s = out[c].dropna()
        if s.empty:
            continue
        gaps = s.index.to_series().diff().dt.days
        breaks = gaps[gaps > max_gap_days]
        if len(breaks):
            s = s.loc[breaks.index[-1]:]      # latest contiguous segment only
        if len(s) >= 90:
            cleaned[c] = s
    return pd.DataFrame(cleaned).reindex(prices.index)


def main() -> None:
    data_dir = config.REPORTS_DIR.parent / "data"
    raw = pd.read_csv(data_dir / "crypto_prices.csv",
                      index_col=0, parse_dates=True)
    dollar_vol = pd.read_csv(data_dir / "crypto_volumes.csv",
                             index_col=0, parse_dates=True)
    prices = clean_crypto(raw)
    dropped = raw.shape[1] - prices.shape[1]
    print(f"Cleaned panel: {prices.shape[1]} coins ({dropped} dropped: "
          f"stables/short segments); gap-broken series truncated to latest segment")
    volumes = (dollar_vol[prices.columns] / prices)
    returns = compute_returns(prices)
    worst = returns.max().max()
    print(f"max single-day return after cleaning: +{worst*100:.0f}%")

    res = run_xsec_strategy(
        prices, volumes, horizon=7, rebal_every=1,
        elig_kwargs=dict(min_price=0.0, min_dollar_vol=1e7, min_history=90),
    )
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
    res.predictions.to_parquet(config.REPORTS_DIR / "preds_crypto2_pit.parquet")

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
              f"vol={s.get('ann_vol'):.3f} turnover={s['ann_turnover']:.1f}x")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "crypto_cycle2.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Crypto cycle 2: cleaned panel, net of costs (UPPER BOUND) ===")
        print(table)


if __name__ == "__main__":
    main()
