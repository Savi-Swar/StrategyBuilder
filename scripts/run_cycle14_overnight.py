"""Cycle 14: overnight/intraday decomposition joins the broad composite.

Features (documented family — clientele separation, Lou-Polk-Skouras):
  on_mom_21/63: cumulative overnight log-return momentum (close->open)
  id_mom_21/63: cumulative intraday log-return momentum (open->close)
  on_id_gap:    on_mom_63 - id_mom_63 (the clientele divergence)
PRE-REGISTERED: broad panel, weekly h=5, features = price + insider +
overnight block; decile construction (arm-C falsified on this panel);
tau {0.25, 0.10}. Baseline: cycle-11 weekly decile +0.047, IC t=3.66.
"""
import numpy as np, pandas as pd
from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns
from quark.ml.xsec import _decile_weights, partial_rebalance_weights, run_xsec_strategy

data_dir = config.REPORTS_DIR.parent / "data"
prices = pd.read_parquet(data_dir / "broad_prices.parquet")
prices.index = pd.to_datetime(prices.index); prices = prices.dropna(how="all")
opens = pd.read_parquet(data_dir / "broad_opens.parquet")
opens.index = pd.to_datetime(opens.index)
opens = opens.reindex(index=prices.index, columns=prices.columns)
dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
volumes = dv / prices
returns = compute_returns(prices)

on_r = np.log(opens / prices.shift(1))          # overnight: prev close -> open
id_r = np.log(prices / opens)                   # intraday: open -> close
extras = {
    "on_mom_21": on_r.rolling(21, min_periods=15).sum(),
    "on_mom_63": on_r.rolling(63, min_periods=42).sum(),
    "id_mom_21": id_r.rolling(21, min_periods=15).sum(),
    "id_mom_63": id_r.rolling(63, min_periods=42).sum(),
}
extras["on_id_gap"] = extras["on_mom_63"] - extras["id_mom_63"]

# insider features (rebuild from cached parse logic — reuse cycle-11 loader)
import importlib.util
spec = importlib.util.spec_from_file_location("c11", "scripts/run_cycle11_insider.py")
c11 = importlib.util.module_from_spec(spec); spec.loader.exec_module.__self__ if False else None
# lighter: re-run the event loader inline
import io, zipfile
def load_ins():
    parts = []
    for zp in sorted((data_dir / "insider").glob("*_form345.zip")):
        try:
            z = zipfile.ZipFile(zp)
            names = {n.upper(): n for n in z.namelist()}
            sub = pd.read_csv(io.BytesIO(z.read(names["SUBMISSION.TSV"])), sep="\t",
                              low_memory=False, usecols=["ACCESSION_NUMBER","FILING_DATE","ISSUERTRADINGSYMBOL"])
            tr = pd.read_csv(io.BytesIO(z.read(names["NONDERIV_TRANS.TSV"])), sep="\t",
                             low_memory=False, usecols=["ACCESSION_NUMBER","TRANS_CODE","TRANS_SHARES","TRANS_PRICEPERSHARE"])
        except Exception: continue
        tr = tr[tr["TRANS_CODE"].isin(["P","S"])]
        m = tr.merge(sub, on="ACCESSION_NUMBER", how="left").dropna(subset=["ISSUERTRADINGSYMBOL","FILING_DATE"])
        val = pd.to_numeric(m["TRANS_SHARES"], errors="coerce") * pd.to_numeric(m["TRANS_PRICEPERSHARE"], errors="coerce")
        sign = np.where(m["TRANS_CODE"] == "P", 1.0, -1.0)
        parts.append(pd.DataFrame({"symbol": m["ISSUERTRADINGSYMBOL"].str.upper().str.strip(),
                                   "filed": pd.to_datetime(m["FILING_DATE"], errors="coerce", format="mixed"),
                                   "value": (val.fillna(0.0)*sign).values, "count": sign}))
    return pd.concat(parts, ignore_index=True).dropna(subset=["filed"])
ev = load_ins(); ev = ev[ev["symbol"].isin(prices.columns)]
val_p = pd.DataFrame(0.0, index=prices.index, columns=prices.columns); cnt_p = val_p.copy()
pos = prices.index.searchsorted(ev["filed"].values, side="right"); keep = pos < len(prices.index)
ev = ev[keep]; pos = pos[keep]
for (i,col),v,c in zip(zip(pos, ev["symbol"].values), ev["value"].values, ev["count"].values):
    j = val_p.columns.get_loc(col); val_p.iat[i,j] += v; cnt_p.iat[i,j] += c
med_dv = dv.rolling(126, min_periods=42).median()
extras["ins_netbuy_180"] = val_p.rolling(180).sum() / med_dv.where(med_dv > 0)
extras["ins_buyers_180"] = cnt_p.rolling(180).sum()

res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                        extra_features=extras,
                        elig_kwargs=dict(min_price=5.0, min_dollar_vol=5e6, min_history=252))
ic_t = float(res.ic.mean()/res.ic.std()*np.sqrt(len(res.ic)))
print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)}) [c11 baseline +0.0194 t=3.66]")
res.predictions.to_parquet(config.REPORTS_DIR / "preds_broad14.parquet")
med = dv.median()
cost = pd.Series(np.where(med > 5e7, 5.0, np.where(med > 1e7, 10.0, 20.0)), index=prices.columns)
targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
for tau in (0.25, 0.10):
    held = partial_rebalance_weights(targets, tau)
    bt = run_weights_backtest(held.reindex(prices.index).ffill(limit=7).fillna(0.0),
                              returns, cost_bps=cost)
    oos = bt.portfolio.index >= res.predictions.index[0]
    s = summary_stats(bt.portfolio[oos])
    print(f"tau={tau}: net sharpe={s['sharpe']:.3f}")
