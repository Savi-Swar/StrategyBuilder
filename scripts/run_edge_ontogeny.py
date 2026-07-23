"""Edge ontogeny: watch documented edges LIVE and DIE in our own data.
For each edge: rolling 252d Sharpe (decile L/S, monthly-formed) or yearly
event-effect. Goal: characterize the ALIVE phase (the calm) vs decay vs
death/inversion — the vital-signs training set."""
import numpy as np, pandas as pd
from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.data.loader import compute_returns

data_dir = config.REPORTS_DIR.parent / "data"
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index); prices = prices.dropna(how="all")
prices = prices.where(prices > 0)
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
opens = pd.read_parquet(data_dir / "broad_opens.parquet")
opens.index = pd.to_datetime(opens.index)
opens = opens.reindex(index=prices.index, columns=prices.columns)
ret = compute_returns(prices).replace([np.inf,-np.inf], np.nan).clip(-0.95, 5.0)
med = dv.median()
cost = pd.Series(np.where(med>5e7,5.0,np.where(med>1e7,10.0,20.0)), index=prices.columns)
elig = (prices>5.0)&(dv.rolling(63,min_periods=21).median()>5e6)&(prices.notna().cumsum()>=252)
month_ends = prices.index.to_series().resample("ME").last().dropna()

def decile_pnl(signal, flip=False):
    tgt = {}
    for dt in month_ends:
        if dt not in signal.index: continue
        row = signal.loc[dt].where(elig.loc[dt]).dropna()
        if len(row) < 200: continue
        r = row.rank(pct=True)
        w = pd.Series(0.0, index=signal.columns)
        lo, sh = r>0.9, r<=0.1
        if flip: lo, sh = sh, lo
        w[lo.index[lo]] = 0.5/lo.sum(); w[sh.index[sh]] = -0.5/sh.sum()
        tgt[dt] = w
    weights = pd.DataFrame(tgt).T.reindex(prices.index).ffill(limit=25).fillna(0.0)
    return run_weights_backtest(weights, ret, cost_bps=cost).portfolio

def vitality(pnl, label):
    roll = pnl.rolling(252).apply(lambda x: x.mean()/x.std()*np.sqrt(252) if x.std()>0 else np.nan)
    yearly = roll.resample("YE").last().dropna()
    line = " ".join(f"{y.year%100:02d}:{v:+.1f}" for y, v in yearly.items())
    # death = first year rolling goes negative and stays (2+ consecutive)
    neg = yearly < 0
    death = None
    vals = list(neg.items())
    for i in range(len(vals)-1):
        if vals[i][1] and vals[i+1][1]: death = vals[i][0].year; break
    print(f"{label:16s} {line}  {'death~'+str(death) if death else 'ALIVE/undead'}")
    return yearly

mom = prices.pct_change(231, fill_method=None).shift(21)
rev = prices.pct_change(21, fill_method=None)
ivol = ret.rolling(63, min_periods=42).std()
mx = ret.rolling(21, min_periods=15).max()
print("=== rolling 252d Sharpe by year-end (our panel, net) ===")
vitality(decile_pnl(mom), "momentum_1993")
vitality(decile_pnl(rev, True), "reversal_1990")
vitality(decile_pnl(ivol, True), "lowvol_2006")
vitality(decile_pnl(mx, True), "max_lottery_2011")
# turn of month (immortal control)
ew = ret.where(elig).mean(axis=1)
idx = prices.index
tom = pd.Series(0.0, index=idx)
mg = pd.Series(idx.to_period("M"), index=idx)
for _, g in mg.groupby(mg):
    d = g.index; tom[list(d[-2:])+list(d[:3])] = 1.0
vitality(ew*tom, "turn_of_month")

# 8-K LARGE drift: yearly event effect from saved events
ev = pd.read_csv(config.REPORTS_DIR / "study_8k_drift_events.csv", parse_dates=["day"])
big = ev[(ev["tier"]=="LARGE") & (ev["react"].abs()>0.05)].copy()
big["signed"] = np.sign(big["react"])*big["drift"]
print("\n=== 8-K LARGE drift: yearly mean signed drift (t) ===")
for y, g in big.groupby(big["day"].dt.year):
    if len(g) < 50: continue
    t = g["signed"].mean()/g["signed"].std()*np.sqrt(len(g))
    print(f"  {y}: {g['signed'].mean()*100:+.2f}% (t={t:+.1f}, n={len(g)})")
