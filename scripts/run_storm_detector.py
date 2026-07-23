"""THE CALM DETECTOR: is the pre-storm state learnable, honestly?
Storm = forward 126d return > +50%. Features = texture of the present only.
Purged walk-forward by year, per-year OOS AUC + top-decile lift.
Then: the learned calm profile (top-scored states vs population)."""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from quark import config

data_dir = config.REPORTS_DIR.parent / "data"
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index); prices = prices.dropna(how="all")
prices = prices.where(prices > 0)
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
ret = prices.ffill(limit=5).pct_change(fill_method=None).where(prices.notna()).clip(-0.95, 5.0)

vol63 = ret.rolling(63, min_periods=42).std()
vol252 = ret.rolling(252, min_periods=126).std()
feats = {
  "vol_compress": vol63/vol252,                                   # the literal calm
  "vol63": vol63*np.sqrt(252),
  "mom21": prices.pct_change(21, fill_method=None),
  "mom63": prices.pct_change(63, fill_method=None),
  "mom252": prices.pct_change(252, fill_method=None),
  "dd_from_high": prices/prices.rolling(252, min_periods=126).max()-1,
  "pos_share63": (ret>0).rolling(63, min_periods=42).mean(),
  "sign_persist": np.sign(prices.pct_change(21, fill_method=None)).rolling(126, min_periods=63).mean(),
  "volu_trend": dv.rolling(63,min_periods=42).median()/dv.rolling(252,min_periods=126).median(),
  "log_dollar_vol": np.log(dv.rolling(63,min_periods=42).median()),
}
fwd126 = prices.shift(-126)/prices - 1
label = (fwd126 > 0.50).astype(float).where(fwd126.notna())
elig = (prices>2.0)&(dv.rolling(63,min_periods=21).median()>2e6)&(prices.notna().cumsum()>=252)

month_ends = prices.index.to_series().resample("ME").last().dropna()
X = pd.concat({k: v.reindex(month_ends).stack() for k,v in feats.items()}, axis=1)
y = label.reindex(month_ends).stack().rename("y")
e = elig.reindex(month_ends).stack().rename("e")
df = X.join(y, how="inner").join(e, how="left")
df = df[df["e"].fillna(False)].drop(columns="e").dropna(subset=["y"])
df.index.names = ["date","sym"]
dates = df.index.get_level_values("date")
print(f"panel: {len(df):,} obs, base storm rate {df['y'].mean():.1%}")

cols = list(feats)
yrs = range(2015, 2026)
aucs, lifts, all_scores = {}, {}, []
for Y in yrs:
    tr = df[(dates.year < Y) & (dates.year >= 2013) & (dates < pd.Timestamp(f"{Y}-01-01") - pd.Timedelta(days=140))]
    te = df[dates.year == Y]
    if len(tr) < 5000 or len(te) < 1000 or te["y"].nunique() < 2: continue
    clf = HistGradientBoostingClassifier(max_iter=150, random_state=0)
    clf.fit(tr[cols], tr["y"])
    p = clf.predict_proba(te[cols])[:,1]
    auc = roc_auc_score(te["y"], p)
    top = te["y"][p >= np.quantile(p, 0.9)]
    lift = top.mean()/te["y"].mean() if te["y"].mean() > 0 else np.nan
    aucs[Y], lifts[Y] = auc, lift
    all_scores.append(pd.DataFrame({"p":p, "y":te["y"].values}, index=te.index))
    print(f"  {Y}: AUC {auc:.3f}  top-decile storm rate {top.mean():.1%} vs base {te['y'].mean():.1%} (lift {lift:.1f}x)")
print(f"\nmean OOS AUC {np.mean(list(aucs.values())):.3f} | mean lift {np.nanmean(list(lifts.values())):.1f}x | positive-lift years {sum(l>1 for l in lifts.values())}/{len(lifts)}")

S = pd.concat(all_scores)
top_states = df.loc[S[S['p'] >= S['p'].quantile(0.95)].index, cols]
print("\nTHE LEARNED CALM (top-5% scored states vs population median):")
for c in cols:
    print(f"  {c:14s} top: {top_states[c].median():+.2f}   pop: {df[c].median():+.2f}")
