"""THE PRIMARY NICHE STUDY: post-announcement drift in micro/small caps.

PRE-REGISTERED (before data complete):
Thesis: earnings information diffuses slowly where no analyst is paid to
read the filing. PEAD is dead in large caps (our cycle 3 + literature);
the niche hypothesis is it survives DOWN the size ladder.

Design:
- Events: 8-K Item 2.02 filing dates (day precision, PIT by construction).
- Direction signal: the ANNOUNCEMENT-DAY market-adjusted return sign/size
  (day 0 = filing date; if filed after close the reaction bleeds to d+1 —
  we use d0..d+1 combined as the reaction window, declared here).
- Drift measure: market-adjusted cumulative return d+2..d+21 in the
  DIRECTION of the reaction (buy positive reactors, short negative).
- Size tiers (63d median dollar volume, causal): LARGE >$50M,
  MID $10-50M, SMALL $5-10M — prediction: drift increases as size falls.
- Reaction filter: |reaction| > 5% (a real surprise), declustered per name
  30 days. Controls: random same-tier days. All reported, both halves
  (2013-2019 / 2019-2026).
"""
import numpy as np, pandas as pd
from quark import config
from quark.data.loader import compute_returns

data_dir = config.REPORTS_DIR.parent / "data"
ann = pd.read_csv(data_dir / "ann_dates_8k.csv", parse_dates=["ann_date"])
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index); prices = prices.dropna(how="all")
prices = prices.where(prices > 0)
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
ret = compute_returns(prices).replace([np.inf, -np.inf], np.nan).clip(-0.95, 5.0)
mkt = ret.mean(axis=1)
adj = ret.sub(mkt, axis=0)
med_dv = dv.rolling(63, min_periods=21).median()
elig = (prices > 1.0) & (med_dv > 2e6)
td = prices.index

ann = ann[ann["ticker"].isin(prices.columns)]
print(f"events on-panel: {len(ann):,} ({ann['ticker'].nunique():,} names), "
      f"{ann['ann_date'].min():%Y-%m} -> {ann['ann_date'].max():%Y-%m}")

def tier(sym, day):
    try:
        v = med_dv.at[day, sym]
    except Exception:
        return None
    if not np.isfinite(v): return None
    return "LARGE" if v > 5e7 else ("MID" if v > 1e7 else
                                    ("SMALL" if v > 2e6 else None))

rows = []
last = {}
for sym, g in ann.groupby("ticker"):
    for d in sorted(g["ann_date"]):
        i = td.searchsorted(d)               # first trading day >= filing date
        if i + 22 >= len(td) or i < 1: continue
        d0 = td[i]
        if sym in last and (d0 - last[sym]).days <= 30: continue
        try:
            if not elig.at[d0, sym]: continue
        except Exception: continue
        t = tier(sym, d0)
        if t is None: continue
        react = adj[sym].iloc[i:i+2].sum()       # d0..d+1 reaction
        drift = adj[sym].iloc[i+2:i+22].sum()    # d+2..d+21
        if not (np.isfinite(react) and np.isfinite(drift)): continue
        last[sym] = d0
        rows.append((d0, sym, t, react, drift))
ev = pd.DataFrame(rows, columns=["day","sym","tier","react","drift"])
print(f"usable declustered events: {len(ev):,}")

def report(sub, label):
    big = sub[sub["react"].abs() > 0.05]
    signed = np.sign(big["react"]) * big["drift"]
    n = len(signed)
    if n < 30:
        print(f"  {label}: n={n} (too few)"); return
    t = signed.mean()/signed.std()*np.sqrt(n)
    tr = signed.clip(signed.quantile(0.05), signed.quantile(0.95))
    print(f"  {label}: n={n:,} signed drift d2-21 mean {signed.mean()*100:+.2f}% "
          f"(t={t:.2f}) median {signed.median()*100:+.2f}% "
          f"trimmed {tr.mean()*100:+.2f}% hit {(signed>0).mean():.0%}")

for era_lbl, a, b in [("2013-2019", "2013-01-01", "2019-06-30"),
                      ("2019-2026", "2019-07-01", "2026-07-01"),
                      ("full     ", "2013-01-01", "2026-07-01")]:
    sub = ev[(ev["day"] >= a) & (ev["day"] <= b)]
    print(f"{era_lbl}:")
    for t in ["LARGE", "MID", "SMALL"]:
        report(sub[sub["tier"] == t], f"{t:5s}")
ev.to_csv(config.REPORTS_DIR / "study_8k_drift_events.csv", index=False)
print("saved reports/study_8k_drift_events.csv")
