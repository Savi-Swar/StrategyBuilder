"""Storm-detector RETURN gate: is the top decile tradable net?"""
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from quark import config
data_dir=config.REPORTS_DIR.parent/"data"
prices=pd.read_parquet(data_dir/"broad_prices.parquet")
prices.index=pd.to_datetime(prices.index); prices=prices.dropna(how="all"); prices=prices.where(prices>0)
dv=pd.read_parquet(data_dir/"broad_volumes.parquet").reindex(prices.index)
ret=prices.ffill(limit=5).pct_change(fill_method=None).where(prices.notna()).clip(-0.95,5.0)
vol63=ret.rolling(63,min_periods=42).std(); vol252=ret.rolling(252,min_periods=126).std()
feats={"vol_compress":vol63/vol252,"vol63":vol63*np.sqrt(252),
 "mom21":prices.pct_change(21,fill_method=None),"mom63":prices.pct_change(63,fill_method=None),
 "mom252":prices.pct_change(252,fill_method=None),
 "dd":prices/prices.rolling(252,min_periods=126).max()-1,
 "pos63":(ret>0).rolling(63,min_periods=42).mean(),
 "sgn":np.sign(prices.pct_change(21,fill_method=None)).rolling(126,min_periods=63).mean(),
 "vtr":dv.rolling(63,min_periods=42).median()/dv.rolling(252,min_periods=126).median(),
 "ldv":np.log(dv.rolling(63,min_periods=42).median())}
fwd=prices.shift(-126)/prices-1
elig=(prices>2.0)&(dv.rolling(63,min_periods=21).median()>2e6)&(prices.notna().cumsum()>=252)
me=prices.index.to_series().resample("ME").last().dropna()
X=pd.concat({k:v.reindex(me).stack() for k,v in feats.items()},axis=1)
y=(fwd>0.5).astype(float).reindex(me).stack().rename("y")
fr=fwd.reindex(me).stack().rename("fwd")
e=elig.reindex(me).stack().rename("e")
df=X.join(y,how="inner").join(fr,how="left").join(e,how="left")
df=df[df["e"].fillna(False)].drop(columns="e").dropna(subset=["y","fwd"])
dates=df.index.get_level_values(0)
cols=list(feats)
COST=0.004*2  # 40bps round trip, these are $2+/2M+ADV names
rows=[]
for Y in range(2015,2026):
    tr=df[(dates.year<Y)&(dates.year>=2013)&(dates<pd.Timestamp(f"{Y}-01-01")-pd.Timedelta(days=140))]
    te=df[dates.year==Y]
    if len(tr)<5000 or len(te)<1000: continue
    clf=HistGradientBoostingClassifier(max_iter=150,random_state=0).fit(tr[cols],tr["y"])
    p=clf.predict_proba(te[cols])[:,1]
    top=te[p>=np.quantile(p,0.95)]
    base=te["fwd"].mean()
    net=top["fwd"]-COST
    rows.append({"yr":Y,"n_top":len(top),"mean_net":net.mean(),"median":net.median(),
                 "base_all":base,"win50":(top["fwd"]>0.5).mean(),"lose50":(top["fwd"]<-0.5).mean()})
R=pd.DataFrame(rows)
print(R.round(3).to_string(index=False))
print(f"\nGATE: mean net fwd-126d return of top-5% states: {R['mean_net'].mean():+.1%} "
      f"vs all-eligible baseline {R['base_all'].mean():+.1%}")
print(f"positive-mean years: {(R['mean_net']>0).sum()}/{len(R)} | positive-vs-baseline years: {(R['mean_net']>R['base_all']).sum()}/{len(R)}")
print(f"avg tail risk in top decile: {R['lose50'].mean():.1%} of names lose >50%")
