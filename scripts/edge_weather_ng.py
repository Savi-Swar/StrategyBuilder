"""Information-edge test 1: realized cold anomalies -> natural gas.

Mechanism: heating degree days (HDD) = physical gas demand. PRE-REGISTERED:
signal = national pop-weighted HDD anomaly vs day-of-year norm computed
from PAST years only (PIT); heating season Nov-Mar; event = top-quintile
cold-anomaly days; measure NG=F cumulative return days +1..+5. Honest
prior: pros trade FORECASTS ahead of realization — expect mostly-priced;
any residual drift is the edge. Data: NOAA CPC daily HDD 2012-2026, free."""
import io, urllib.request
import numpy as np, pandas as pd
from quark.data.loader import compute_returns, load_prices

frames = []
for yr in range(2012, 2027):
    url = f"https://ftp.cpc.ncep.noaa.gov/htdocs/degree_days/weighted/daily_data/{yr}/Population.Heating.txt"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "quark-research saviswarup@gmail.com"})
        raw = urllib.request.urlopen(req, timeout=30).read().decode()
    except Exception as e:
        print(f"  {yr}: {type(e).__name__}")
        continue
    lines = [l for l in raw.splitlines() if l and (l[0].isdigit() or l.startswith("Region"))]
    hdrs = [l for l in lines if l.startswith("Region")]
    if not hdrs:
        continue
    hdr = hdrs[0].split("|")[1:]
    dates = pd.to_datetime(hdr, format="%Y%m%d")
    rows = {}
    for l in lines:
        if l.startswith("Region"): continue
        parts = l.split("|")
        rows[parts[0]] = [float(x) if x.strip() else np.nan for x in parts[1:len(dates)+1]]
    df = pd.DataFrame(rows, index=dates)
    frames.append(df.mean(axis=1).rename("hdd"))   # national proxy: mean of divisions
hdd = pd.concat(frames).sort_index()
print(f"HDD series: {len(hdd)} days, {hdd.index[0].date()} -> {hdd.index[-1].date()}")

# PIT seasonal norm: expanding day-of-year mean using ONLY past years
doy = hdd.index.dayofyear
norm = pd.Series(index=hdd.index, dtype=float)
for i, (dt, v) in enumerate(hdd.items()):
    past = hdd[(hdd.index < dt - pd.Timedelta(days=300))]
    same_doy = past[np.abs(past.index.dayofyear - doy[i]) <= 3]
    norm.iloc[i] = same_doy.mean() if len(same_doy) >= 6 else np.nan
anom = (hdd - norm)
z = anom / anom.rolling(365, min_periods=180).std()

ng = load_prices(tickers=["NG=F"], start="2012-01-01")["NG=F"].dropna()
ret = ng.pct_change()
season = z[(z.index.month.isin([11,12,1,2,3]))].dropna()
season = season[season.index >= "2014-01-01"]     # after norm warm-up
# event: top-quintile cold anomaly
thresh = season.expanding(min_periods=100).quantile(0.8)
events = season[(season > thresh) & thresh.notna()].index
print(f"cold-anomaly events: {len(events)}")
cums = []
for e in events:
    fut = ret[ret.index > e].iloc[:5]
    if len(fut) == 5:
        cums.append(fut.sum())
cums = pd.Series(cums)
t = cums.mean()/cums.std()*np.sqrt(len(cums))
print(f"NG=F cum return d+1..+5 after cold shock: mean {cums.mean()*100:+.2f}% "
      f"(t={t:.2f}, n={len(cums)})")
# control: same stat on random in-season days
rng = np.random.default_rng(0)
ctrl_days = rng.choice(season.index, size=min(len(events)*3, len(season)), replace=False)
cc = []
for e in pd.DatetimeIndex(ctrl_days):
    fut = ret[ret.index > e].iloc[:5]
    if len(fut) == 5: cc.append(fut.sum())
cc = pd.Series(cc)
print(f"control (random in-season days): mean {cc.mean()*100:+.2f}% (n={len(cc)})")
