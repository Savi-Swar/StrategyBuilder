"""Cycle-13 verification gauntlet: control, stability, correlation."""
import numpy as np, pandas as pd
from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.ml.xsec import _decile_weights, partial_rebalance_weights, run_xsec_strategy
from quark.universe import load_universe

u = load_universe(); u = u[u["tradable"] & ~u["hindsight_picked"].fillna(False)]
prices = load_prices(tickers=list(u.index), start="2005-01-01").dropna(how="all")
volumes = prices.notna().astype(float)
returns = compute_returns(prices)
cost = u["cost_bps"].astype(float)

# 1) Shuffled-label control (same config)
res_s = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1, top_frac=0.15,
                          shuffle_labels=True,
                          elig_kwargs=dict(min_price=0.0, min_dollar_vol=0.0, min_history=252))
t_s = res_s.predictions.apply(_decile_weights, axis=1, top_frac=0.15)
held = partial_rebalance_weights(t_s, 0.25)
bt_s = run_weights_backtest(held.reindex(prices.index).ffill(limit=7).fillna(0.0),
                            returns, cost_bps=cost)
oos = bt_s.portfolio.index >= res_s.predictions.index[0]
print(f"shuffled control: sharpe {summary_stats(bt_s.portfolio[oos])['sharpe']:.3f} "
      f"(should be ~<=0)")

# 2) Real book: yearly Sharpes + correlation to equity champion
preds = pd.read_parquet(config.REPORTS_DIR / "preds_multiasset13.parquet")
t = preds.apply(_decile_weights, axis=1, top_frac=0.15)
held = partial_rebalance_weights(t, 0.25)
bt = run_weights_backtest(held.reindex(prices.index).ffill(limit=7).fillna(0.0),
                          returns, cost_bps=cost)
r = bt.portfolio[bt.portfolio.index >= preds.index[0]]
yearly = r.groupby(r.index.year).apply(
    lambda x: x.mean()/x.std()*np.sqrt(252) if x.std() > 0 else np.nan)
print("yearly sharpe:", {k: round(v, 2) for k, v in yearly.items()})
print(f"positive years: {(yearly > 0).sum()}/{yearly.notna().sum()}")

wf = pd.read_csv(config.REPORTS_DIR / "cycle9_wf_returns.csv", index_col=0, parse_dates=True).iloc[:,0]
both = pd.concat([r.rename("ma"), wf.rename("eq")], axis=1).dropna()
print(f"corr to equity WF stream: {both['ma'].corr(both['eq']):+.3f}")
r.to_csv(config.REPORTS_DIR / "cycle13_returns.csv")
