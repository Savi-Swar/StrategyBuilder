"""Edge archaeology: replicate 10 published anomalies on our broad panel
and watch the lifecycle with our own eyes.

Each edge: publication year, simple canonical construction (no ML — the
published recipe), monthly-formed decile L/S, gross AND net (tiered costs),
measured on 2013-2019 vs 2019-2026 halves. Expectation from verified decay
literature: most should be dead or dying; anything alive post-2019 in our
panel is interesting. This is intuition training, not strategy search —
NO tuning, one canonical spec each, all reported.

Edges: (pub year)
  1990 short-term reversal (Jegadeesh): prev-month return, SHORT winners
  1993 momentum 12-2 (Jegadeesh-Titman)
  2004 52-week-high proximity (George-Hwang)
  2006 idiosyncratic-vol (Ang et al): LOW vol wins
  2011 MAX lottery effect (Bali): low max-daily-return wins
  2016 overnight-intraday clientele gap (Lou-Polk-Skouras, on/id 63d)
  1998 insider net buying (Lakonishok-Lee, our Form 4 panel, 180d)
  1968 turn-of-month seasonality (timing overlay, long-only EW panel)
  2008 asset-growth via proxy: 12m share-count growth reversed (issuance)
  1996 dollar-volume/illiquidity premium (Brennan et al): LOW $vol wins
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns

data_dir = config.REPORTS_DIR.parent / "data"
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index)
prices = prices.dropna(how="all")
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
opens = pd.read_parquet(data_dir / "broad_opens.parquet")
opens.index = pd.to_datetime(opens.index)
opens = opens.reindex(index=prices.index, columns=prices.columns)
returns = compute_returns(prices)
med = dv.median()
cost = pd.Series(np.where(med > 5e7, 5.0, np.where(med > 1e7, 10.0, 20.0)),
                 index=prices.columns)
elig = ((prices > 5.0)
        & (dv.rolling(63, min_periods=21).median() > 5e6)
        & (prices.notna().cumsum() >= 252))

month_ends = prices.index.to_series().resample("ME").last().dropna()


def decile_ls(signal: pd.DataFrame, flip: bool = False) -> pd.Series:
    """Monthly decile L/S from a daily signal panel; returns net daily P&L."""
    tgt = {}
    for dt in month_ends:
        if dt not in signal.index:
            continue
        row = signal.loc[dt].where(elig.loc[dt]).dropna()
        if len(row) < 200:
            continue
        r = row.rank(pct=True)
        w = pd.Series(0.0, index=signal.columns)
        long, short = r > 0.9, r <= 0.1
        if flip:
            long, short = short, long
        w[long.index[long]] = 0.5 / long.sum()
        w[short.index[short]] = -0.5 / short.sum()
        tgt[dt] = w
    weights = pd.DataFrame(tgt).T.reindex(prices.index).ffill(limit=25).fillna(0.0)
    bt = run_weights_backtest(weights, returns, cost_bps=cost)
    return bt.portfolio


mom_1m = prices.pct_change(21, fill_method=None)
mom_12_2 = prices.pct_change(231, fill_method=None).shift(21)
hi52 = prices / prices.rolling(252, min_periods=200).max()
ivol = returns.rolling(63, min_periods=42).std()
maxret = returns.rolling(21, min_periods=15).max()
on_r = np.log(opens / prices.shift(1))
id_r = np.log(prices / opens)
on_gap = on_r.rolling(63, min_periods=42).sum() - id_r.rolling(63, min_periods=42).sum()
lowdv = dv.rolling(63, min_periods=42).median()

EDGES = {
    "reversal_1990": (mom_1m, True),
    "momentum_1993": (mom_12_2, False),
    "hi52_2004": (hi52, False),
    "lowvol_2006": (ivol, True),
    "max_lottery_2011": (maxret, True),
    "overnight_2016": (on_gap, False),
    "illiquidity_1996": (lowdv, True),
}

# insider (1998): reuse cached parse via cycle-14's panels if available
try:
    ins = pd.read_parquet(config.REPORTS_DIR / "preds_broad14.parquet")  # placeholder no
except Exception:
    ins = None

rows = {}
halves = [("2013-2019", "2013-01-01", "2019-06-30"),
          ("2019-2026", "2019-07-01", "2026-07-01")]
for name, (sig, flip) in EDGES.items():
    pnl = decile_ls(sig, flip)
    rec = {}
    for label, a, b in halves:
        r = pnl[(pnl.index >= a) & (pnl.index <= b)]
        rec[f"sharpe_{label}"] = float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan
    full = pnl[pnl.index >= "2013-01-01"]
    rec["sharpe_full"] = float(full.mean() / full.std() * np.sqrt(252))
    rows[name] = rec
    print(f"{name:ame>20s}" if False else f"{name:20s} "
          f"13-19: {rec['sharpe_2013-2019']:+.2f}  "
          f"19-26: {rec['sharpe_2019-2026']:+.2f}  full: {rec['sharpe_full']:+.2f}")

# turn-of-month (1968): long EW eligible book only during last 2 + first 3 tds
ew = returns.where(elig).mean(axis=1)
idx = prices.index
tom = pd.Series(0.0, index=idx)
month_grp = pd.Series(idx.to_period("M"), index=idx)
for _, g in month_grp.groupby(month_grp):
    days = g.index
    sel = list(days[-2:]) + list(days[:3])
    tom[sel] = 1.0
tom_pnl = ew * tom
rec = {}
for label, a, b in halves:
    r = tom_pnl[(tom_pnl.index >= a) & (tom_pnl.index <= b)]
    rec[f"sharpe_{label}"] = float(r.mean() / r.std() * np.sqrt(252)) if r.std() > 0 else np.nan
rec["sharpe_full"] = float(tom_pnl[tom_pnl.index >= "2013-01-01"].mean()
                           / tom_pnl[tom_pnl.index >= "2013-01-01"].std() * np.sqrt(252))
rows["turn_of_month_1968"] = rec
print(f"{'turn_of_month_1968':20s} 13-19: {rec['sharpe_2013-2019']:+.2f}  "
      f"19-26: {rec['sharpe_2019-2026']:+.2f}  full: {rec['sharpe_full']:+.2f}")

table = pd.DataFrame(rows).T
table.to_csv(config.REPORTS_DIR / "edge_archaeology.csv")
print("\nsaved reports/edge_archaeology.csv")
