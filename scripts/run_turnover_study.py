"""Pre-registered turnover study: no-trade bands on the flagship model.

The weekly cross-sectional signal is real (IC +0.0172, t=3.35) but weekly
decile re-formation spends most of it on costs. A no-trade band adds
hysteresis: a name ENTERS the book in the extreme decile (unchanged rule)
but is only EXITED once its rank has decayed by a fixed gap — trading the
freshness of the signal against the cost of chasing it.

TRIAL ACCOUNTING — registered before results were seen:
  exit gaps 0.15 / 0.20 / 0.30 rank points (3 trials + the weekly and
  monthly baselines already counted in the Study 2 registry). Nothing else
  was tried; whatever the table says ships.

One model fit (identical to run_xsec.py primary config); every variant is a
different weight rule over the SAME stored walk-forward predictions, so the
comparison is exact, not noise between refits.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import load_sp500_tickers
from quark.ml.xsec import run_xsec_strategy
from quark.universe import EQUITY_COST_BPS

EXIT_GAPS = [0.15, 0.20, 0.30]  # pre-registered; do not add post hoc


def band_weights(predictions: pd.DataFrame, exit_gap: float) -> pd.DataFrame:
    """Hysteresis book: enter in the extreme decile, hold until rank decays
    past the gap (or the name leaves the prediction universe)."""
    longs: set = set()
    shorts: set = set()
    rows = {}
    for dt, row in predictions.iterrows():
        pct = row.rank(pct=True).dropna()
        longs = {t for t in longs
                 if t in pct.index and pct[t] > 0.90 - exit_gap}
        shorts = {t for t in shorts
                  if t in pct.index and pct[t] <= 0.10 + exit_gap}
        longs |= set(pct.index[pct > 0.90])
        shorts |= set(pct.index[pct <= 0.10])
        w = pd.Series(0.0, index=predictions.columns)
        if longs and shorts:
            w[list(longs)] = 0.5 / len(longs)
            w[list(shorts)] = -0.5 / len(shorts)
        rows[dt] = w
    return pd.DataFrame(rows).T


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
    oos_start = res.predictions.index[0]

    def evaluate(name: str, weights_rebal: pd.DataFrame) -> pd.Series:
        daily = (weights_rebal.reindex(prices.index).ffill(limit=7)
                 .fillna(0.0))
        bt = run_weights_backtest(daily, returns, cost_bps=EQUITY_COST_BPS)
        r = bt.portfolio[bt.portfolio.index >= oos_start]
        s = summary_stats(r)
        s["ann_turnover"] = bt.stats["ann_turnover"]
        s["cost_drag_ann"] = bt.stats["cost_drag_ann"]
        s["avg_names_held"] = float(
            (weights_rebal != 0).sum(axis=1).mean())
        print(f"  {name:<22} sharpe {s['sharpe']:+.2f}  "
              f"turnover {s['ann_turnover']:.1f}x  "
              f"cost drag {s['cost_drag_ann'] * 1e4:.0f} bps/yr  "
              f"names {s['avg_names_held']:.0f}")
        return pd.Series(s, name=name)

    print("Evaluating variants over identical predictions:")
    rows = [evaluate("weekly_reform (base)",
                     res.predictions.apply(
                         lambda r: _base_weights(r), axis=1))]
    for gap in EXIT_GAPS:
        rows.append(evaluate(f"band_exit_{int(gap * 100)}",
                             band_weights(res.predictions, gap)))

    table = pd.DataFrame(rows)
    out = config.REPORTS_DIR / "turnover_study.csv"
    table.to_csv(out)
    print(f"\nWrote {out}")
    print(table[["cagr", "ann_vol", "sharpe", "max_dd",
                 "ann_turnover", "cost_drag_ann", "avg_names_held"]]
          .to_string(float_format=lambda v: f"{v: .3f}"))


def _base_weights(preds_row: pd.Series) -> pd.Series:
    r = preds_row.rank(pct=True)
    long, short = r > 0.90, r <= 0.10
    w = pd.Series(0.0, index=preds_row.index)
    if long.sum() and short.sum():
        w[long] = 0.5 / long.sum()
        w[short] = -0.5 / short.sum()
    return w


if __name__ == "__main__":
    main()
