"""Cycle 12: construction overhaul — the layer no cycle ever touched.

Evidence (logged, cycles 1-10a): rank-IC real on all universes; decile
curve monotone D1->D8 and REVERSING at D10; decile books bet only on the
flattest/reversing slices. Theory (verified): transfer coefficient — book
construction determines how much of the IC becomes IR.

PRE-REGISTERED ARMS (broad-panel cached predictions, tau=0.10, no retrain):
  A) decile (baseline, cycle-10a reproduction)
  B) rank-linear: w proportional to (rank_pct - 0.5), all names — harvests
     the full monotone interior instead of the extremes; textbook max-TC
     construction under (approximately) linear alpha-in-rank
  C) B + inverse-vol scaling: w_i / sigma_i(63d), renormalized — same
     signal, less small-cap noise (craftsmanship: risk-weight the bet)
  D) C + beta-neutralization: subtract the component of w along the
     cross-sectional beta vector (rolling 126d beta to the equal-weight
     panel return) — dollar-neutral is not beta-neutral (verified)
All arms: +-50% gross per side normalization, same GP tau=0.10 partial
rebalancing, tiered costs. Also reported on the S&P monthly cached preds
(fund features, tau=0.25) as an out-of-family check.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns
from quark.ml.xsec import _decile_weights, partial_rebalance_weights


def normalize(w: pd.Series) -> pd.Series:
    pos, neg = w.clip(lower=0), (-w).clip(lower=0)
    out = pd.Series(0.0, index=w.index)
    if pos.sum() > 0:
        out += 0.5 * pos / pos.sum()
    if neg.sum() > 0:
        out -= 0.5 * neg / neg.sum()
    return out


def build_targets(preds, arm, vol=None, beta=None):
    rows = {}
    for dt, row in preds.iterrows():
        r = row.rank(pct=True).dropna()
        if len(r) < 50:
            continue
        if arm == "A":
            w = _decile_weights(row, 0.10)
        else:
            w = (r - r.mean()).reindex(preds.columns).fillna(0.0)
            if arm in ("C", "D") and vol is not None:
                v = vol.loc[:dt].iloc[-1].reindex(preds.columns)
                w = (w / v.where(v > 0)).fillna(0.0)
            if arm == "D" and beta is not None:
                b = beta.loc[:dt].iloc[-1].reindex(preds.columns).fillna(0.0)
                denom = float((b * b).sum())
                if denom > 0:
                    w = w - b * float((w * b).sum()) / denom
            w = normalize(w)
        rows[dt] = w
    return pd.DataFrame(rows).T


def evaluate(preds, prices, returns, cost_bps, tau, ffl, vol, beta, label):
    out = {}
    oos_start = preds.index[0]
    for arm in ["A", "B", "C", "D"]:
        targets = build_targets(preds, arm, vol, beta)
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=cost_bps)
        oos = bt.portfolio.index >= oos_start
        s = summary_stats(bt.portfolio[oos])
        n_years = oos.sum() / config.ANN_FACTOR
        s["ann_turnover"] = float(bt.turnover[oos].sum() / n_years)
        s["cost_drag_ann"] = float(bt.costs.sum(axis=1)[oos].sum() / n_years)
        out[f"{label}_{arm}"] = s
        print(f"  {label} arm {arm}: net sharpe={s.get('sharpe'):.3f} "
              f"vol={s.get('ann_vol'):.3f}")
    return out


def main() -> None:
    data_dir = config.REPORTS_DIR.parent / "data"
    rows = {}

    # --- Broad panel, weekly preds, tau=0.10
    prices = pd.read_parquet(data_dir / "broad_prices.parquet")
    prices.index = pd.to_datetime(prices.index)
    prices = prices.dropna(how="all")
    dv = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
    returns = compute_returns(prices)
    med = dv.median()
    cost = pd.Series(np.where(med > 5e7, 5.0, np.where(med > 1e7, 10.0, 20.0)),
                     index=prices.columns)
    vol63 = returns.rolling(63, min_periods=42).std()
    mkt = returns.mean(axis=1)
    cov = returns.rolling(126, min_periods=63).cov(mkt)
    beta = cov.div(mkt.rolling(126, min_periods=63).var(), axis=0)
    preds = pd.read_parquet(config.REPORTS_DIR / "preds_broad10a.parquet")
    print("Broad panel arms:")
    rows.update(evaluate(preds, prices, returns, cost, 0.10, 7,
                         vol63, beta, "broad_w"))

    # --- S&P PIT monthly preds (fund features), tau=0.25 — out-of-family check
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    from quark.data.loader import load_prices
    from quark.data.quality import clean_panel, quality_report
    sp = load_prices(tickers=sorted(pit["ticker"].unique()), start="2005-01-01")
    sp = clean_panel(sp, quality_report(sp)).dropna(how="all")
    rsp = compute_returns(sp)
    vol63s = rsp.rolling(63, min_periods=42).std()
    mkts = rsp.mean(axis=1)
    covs = rsp.rolling(126, min_periods=63).cov(mkts)
    betas = covs.div(mkts.rolling(126, min_periods=63).var(), axis=0)
    predm = pd.read_parquet(config.REPORTS_DIR / "preds_monthly_fund_pit.parquet")
    print("S&P monthly arms:")
    rows.update(evaluate(predm, sp, rsp, 5.0, 0.25, 28,
                         vol63s, betas, "sp_m"))

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle12_construction.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 12: construction arms (A=decile baseline) ===")
        print(table)


if __name__ == "__main__":
    main()
