"""Two gate measurements on cached predictions.
A) Cycle-13 walk-forward config selection (3 candidates, yearly, 2015+).
B) Insider-enhanced broad preds x arm-C construction (tau=0.10)."""
import numpy as np, pandas as pd
from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.ml.xsec import _decile_weights, partial_rebalance_weights
from quark.universe import load_universe

# ---------- A) cycle-13 WF gate ----------
u = load_universe(); u = u[u["tradable"] & ~u["hindsight_picked"].fillna(False)]
prices = load_prices(tickers=list(u.index), start="2005-01-01").dropna(how="all")
returns = compute_returns(prices)
cost = u["cost_bps"].astype(float)
preds = pd.read_parquet(config.REPORTS_DIR / "preds_multiasset13.parquet")
vol63 = returns.rolling(63, min_periods=42).std()

def armc_targets(p):
    rows = {}
    for dt, row in p.iterrows():
        r = row.rank(pct=True).dropna()
        if len(r) < 20: continue
        w = (r - r.mean()).reindex(p.columns).fillna(0.0)
        v = vol63.loc[:dt].iloc[-1].reindex(p.columns)
        w = (w / v.where(v > 0)).fillna(0.0)
        pos, neg = w.clip(lower=0), (-w).clip(lower=0)
        o = pd.Series(0.0, index=w.index)
        if pos.sum() > 0: o += 0.5*pos/pos.sum()
        if neg.sum() > 0: o -= 0.5*neg/neg.sum()
        rows[dt] = o
    return pd.DataFrame(rows).T

streams = {}
for name, tgt, tau in [("decile_t.25", preds.apply(_decile_weights, axis=1, top_frac=0.15), 0.25),
                       ("armC_t1.0", armc_targets(preds), 1.00),
                       ("armC_t.25", armc_targets(preds), 0.25)]:
    held = partial_rebalance_weights(tgt, tau)
    bt = run_weights_backtest(held.reindex(prices.index).ffill(limit=7).fillna(0.0),
                              returns, cost_bps=cost)
    streams[name] = bt.portfolio[bt.portfolio.index >= preds.index[0]]

start = preds.index[0]
chained = []
for year in range(2015, 2027):
    tr_end, te_end = pd.Timestamp(f"{year-1}-12-31"), pd.Timestamp(f"{year}-12-31")
    best, bs = None, -np.inf
    for n, s in streams.items():
        tr = s[(s.index >= start) & (s.index <= tr_end)]
        if tr.std() > 0 and tr.mean()/tr.std() > bs:
            best, bs = n, tr.mean()/tr.std()
    te = streams[best][(streams[best].index > tr_end) & (streams[best].index <= te_end)]
    chained.append(te)
wf = pd.concat(chained).sort_index()
s = summary_stats(wf)
print(f"A) cycle-13 WALK-FORWARD 2015-2026: sharpe {s['sharpe']:.3f} "
      f"(in-sample-selected was 0.711)")

# ---------- B) insider preds x arm-C ----------
bp = pd.read_parquet(config.REPORTS_DIR.parent / "data" / "broad_prices.parquet")
bp.index = pd.to_datetime(bp.index); bp = bp.dropna(how="all")
dv = pd.read_parquet(config.REPORTS_DIR.parent / "data" / "broad_volumes.parquet").reindex(bp.index)
bret = compute_returns(bp)
med = dv.median()
bcost = pd.Series(np.where(med > 5e7, 5.0, np.where(med > 1e7, 10.0, 20.0)), index=bp.columns)
bvol = bret.rolling(63, min_periods=42).std()
ip = pd.read_parquet(config.REPORTS_DIR / "preds_broad11_insider.parquet")
rows = {}
for dt, row in ip.iterrows():
    r = row.rank(pct=True).dropna()
    if len(r) < 50: continue
    w = (r - r.mean()).reindex(ip.columns).fillna(0.0)
    v = bvol.loc[:dt].iloc[-1].reindex(ip.columns)
    w = (w / v.where(v > 0)).fillna(0.0)
    pos, neg = w.clip(lower=0), (-w).clip(lower=0)
    o = pd.Series(0.0, index=w.index)
    if pos.sum() > 0: o += 0.5*pos/pos.sum()
    if neg.sum() > 0: o -= 0.5*neg/neg.sum()
    rows[dt] = o
tgt = pd.DataFrame(rows).T
held = partial_rebalance_weights(tgt, 0.10)
bt = run_weights_backtest(held.reindex(bp.index).ffill(limit=7).fillna(0.0),
                          bret, cost_bps=bcost)
r2 = bt.portfolio[bt.portfolio.index >= ip.index[0]]
s2 = summary_stats(r2)
print(f"B) insider x arm-C tau=0.10: sharpe {s2['sharpe']:.3f} "
      f"vol {s2['ann_vol']:.3f} (decile was +0.047)")
corr = float(r2.corr(streams['decile_t.25']))
print(f"   corr(insider-equity book, multiasset book): {corr:+.3f}")
