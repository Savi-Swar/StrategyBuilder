"""WSB attention study — EXACTLY as pre-registered in RESEARCH_NOTES
(2026-07-23). H1: spike -> fade d+5..+20 in small names. H2: momentum
d+1..+3. Counts only (scores are lookahead). Blocklist frozen. Full
sample AND 2022+ reported. Expectation set in advance: null/corpse likely."""
import re
import numpy as np, pandas as pd
from quark import config
from quark.data.loader import compute_returns

data_dir = config.REPORTS_DIR.parent / "data"
wsb = pd.read_csv(data_dir / "wsb_top_daily.csv")
wsb["day"] = pd.to_datetime(wsb["day"])
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index); prices = prices.dropna(how="all")
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
ret = compute_returns(prices)
mkt = ret.mean(axis=1)

BLOCK = {"A","DD","IT","CEO","ON","ALL","ARE","FOR","GO","NOW","OPEN","REAL",
         "SO","OUT","EAT","BIG","CAN","HAS","ANY","RH","YOLO","I","U","DO",
         "BE","AM","PM","EOD","ATH","IMO","FOMO","WSB","USA","SEC","FED","ETF"}
symbols = set(s for s in prices.columns if isinstance(s, str) and s.isalpha())
cash_re = re.compile(r"\$([A-Za-z]{1,5})\b")
bare_re = re.compile(r"\b([A-Z]{2,5})\b")

rows = []
for day, g in wsb.groupby("day"):
    counts = {}
    for t in g["title"].fillna(""):
        seen = set()
        for m in cash_re.findall(t):
            s = m.upper()
            if s in symbols: seen.add(s)
        for m in bare_re.findall(t):
            if m in symbols and m not in BLOCK: seen.add(m)
        for s in seen: counts[s] = counts.get(s, 0) + 1
    for s, c in counts.items():
        rows.append((day, s, c))
m = pd.DataFrame(rows, columns=["day","sym","n"])
mentions = m.pivot_table(index="day", columns="sym", values="n", aggfunc="sum")
mentions = mentions.reindex(pd.date_range(mentions.index[0], mentions.index[-1])).fillna(0.0)
print(f"mention panel: {mentions.shape[1]} tickers, top: "
      f"{mentions.sum().sort_values(ascending=False).head(8).astype(int).to_dict()}")

# map to trading days (weekend mentions roll to next trading day)
td = prices.index
pos = td.searchsorted(mentions.index, side="left")
keep = pos < len(td)
mt = mentions[keep].groupby(td[pos[keep]]).sum()

mu = mt.rolling(63, min_periods=30).mean()
sd = mt.rolling(63, min_periods=30).std().clip(lower=0.5)
z = (mt - mu) / sd
small = dv.rolling(63, min_periods=21).median() < 2.5e7   # small-name proxy
elig = (prices > 5.0) & (dv.rolling(63, min_periods=21).median() > 5e6)

def adj_cum(sym, day, a, b):
    r = (ret[sym] - mkt)[ret.index > day].iloc[a-1:b]
    return float(r.sum()) if len(r) == b-a+1 else np.nan

def run_era(era_start, label):
    ev = []
    last = {}
    zz = z[z.index >= era_start]
    for day in zz.index:
        row = zz.loc[day]
        hits = row[(row > 2.0) & (mt.loc[day] >= 3)].index
        for s in hits:
            if s not in prices.columns: continue
            if not (small.at[day, s] and elig.at[day, s]): continue
            if s in last and (day - last[s]).days <= 7: continue
            last[s] = day
            ev.append((day, s))
    h2 = pd.Series([adj_cum(s, d, 1, 3) for d, s in ev]).dropna()
    h1 = pd.Series([adj_cum(s, d, 5, 20) for d, s in ev]).dropna()
    def t(x): return x.mean()/x.std()*np.sqrt(len(x)) if len(x) > 5 else np.nan
    print(f"{label}: events={len(ev)}  "
          f"H2 mom d1-3: {h2.mean()*100:+.2f}% (t={t(h2):.2f})  "
          f"H1 fade d5-20: {h1.mean()*100:+.2f}% (t={t(h1):.2f})")
    return ev

ev_full = run_era(pd.Timestamp("2019-06-01"), "full sample")
ev_post = run_era(pd.Timestamp("2022-01-01"), "2022+      ")
# control: random small-name eligible days
rng = np.random.default_rng(1)
days = z.index[z.index >= "2019-06-01"]
ctrl = []
syms = [s for s in mt.columns if s in prices.columns]
while len(ctrl) < 400:
    d = days[rng.integers(len(days))]; s = syms[rng.integers(len(syms))]
    try:
        if small.at[d, s] and elig.at[d, s]: ctrl.append((d, s))
    except Exception: pass
c1 = pd.Series([adj_cum(s, d, 5, 20) for d, s in ctrl]).dropna()
print(f"control d5-20: {c1.mean()*100:+.2f}% (n={len(c1)})")
