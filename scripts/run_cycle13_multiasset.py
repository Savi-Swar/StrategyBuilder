"""Cycle 13: cross-sectional multi-asset (the pond Study 1 never fished).

Study 1 traded these 81 instruments TIME-SERIES (per-instrument timing) and
died honestly. This ranks them AGAINST EACH OTHER weekly — relative value
across asset classes, the managed-futures construction with documented
CTA-tier results. PRE-REGISTERED: h=5 weekly; excl hindsight_picked;
top_frac=0.15 decile-style baseline (tau .25) + arm-C rank-linear/inv-vol
construction (tau {1.0, .25}); per-class costs from universe. FX volume
absent -> eligibility price-only (documented). Carry features = cycle 13b.
"""
import numpy as np, pandas as pd
from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.ml.xsec import _decile_weights, partial_rebalance_weights, run_xsec_strategy
from quark.universe import load_universe

def main():
    u = load_universe()
    u = u[u["tradable"] & ~u["hindsight_picked"].fillna(False)]
    prices = load_prices(tickers=list(u.index), start="2005-01-01").dropna(how="all")
    volumes = prices.notna().astype(float)          # FX has no volume; price-only elig
    returns = compute_returns(prices)
    cost = u["cost_bps"].astype(float)
    print(f"{prices.shape[1]} instruments, classes: {u.groupby('asset_class').size().to_dict()}")

    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                            top_frac=0.15,
                            elig_kwargs=dict(min_price=0.0, min_dollar_vol=0.0, min_history=252))
    ic_t = float(res.ic.mean()/res.ic.std()*np.sqrt(len(res.ic)))
    print(f"IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)}) "
          f"names/wk {res.predictions.notna().sum(axis=1).median():.0f}")
    res.predictions.to_parquet(config.REPORTS_DIR / "preds_multiasset13.parquet")

    vol63 = returns.rolling(63, min_periods=42).std()
    def arm_c_targets(preds):
        rows = {}
        for dt, row in preds.iterrows():
            r = row.rank(pct=True).dropna()
            if len(r) < 20: continue
            w = (r - r.mean()).reindex(preds.columns).fillna(0.0)
            v = vol63.loc[:dt].iloc[-1].reindex(preds.columns)
            w = (w / v.where(v > 0)).fillna(0.0)
            pos, neg = w.clip(lower=0), (-w).clip(lower=0)
            out = pd.Series(0.0, index=w.index)
            if pos.sum() > 0: out += 0.5*pos/pos.sum()
            if neg.sum() > 0: out -= 0.5*neg/neg.sum()
            rows[dt] = out
        return pd.DataFrame(rows).T

    oos_start = res.predictions.index[0]
    rows = {}
    arms = [("decile_t0.25", res.predictions.apply(_decile_weights, axis=1, top_frac=0.15), 0.25),
            ("armC_t1.00", arm_c_targets(res.predictions), 1.00),
            ("armC_t0.25", arm_c_targets(res.predictions), 0.25)]
    for name, targets, tau in arms:
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=7).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=cost)
        oos = bt.portfolio.index >= oos_start
        s = summary_stats(bt.portfolio[oos])
        n_years = oos.sum()/config.ANN_FACTOR
        s["ann_turnover"] = float(bt.turnover[oos].sum()/n_years)
        s["ic_mean"], s["ic_t"] = float(res.ic.mean()), ic_t
        rows[name] = s
        print(f"{name}: net sharpe={s.get('sharpe'):.3f} vol={s.get('ann_vol'):.3f}")
    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle13_multiasset.csv")
    with pd.option_context("display.width", 200, "display.float_format", "{:.4f}".format):
        print(table)

if __name__ == "__main__":
    main()
