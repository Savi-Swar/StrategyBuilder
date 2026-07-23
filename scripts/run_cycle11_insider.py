"""Cycle 11: insider trading (SEC Form 4) — first behavioral family.

Data: SEC structured insider-transaction quarterly sets (data/insider/*.zip,
2012q2-2026q2). Open-market purchases (code P) and sales (S) only —
legally-informed flow. PIT via FILING_DATE (Form 4s are due within 2
business days of the trade since 2002, so staleness is minimal — unlike
the 10-Q trap).

Features (per name, daily, PIT):
  ins_netbuy_180: signed dollar value (P minus S) filed in trailing 180
    calendar days, / trailing median daily dollar volume (scale-free)
  ins_buyers_180: count of P filings minus S filings, trailing 180d
Literature expectation (unverified in our research runs — we generate the
evidence): purchases predict positively, strongest in smaller caps.

PRE-REGISTERED: broad panel, price features + the 2 insider features;
configs: weekly h=5 tau=0.10 and monthly h=21 (rebal 4) tau=0.25.
Baselines: cycle-10a weekly tau0.10 = −0.07, IC +0.0173 (t=3.11).
"""

import io
import zipfile

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns
from quark.ml.xsec import (
    _decile_weights,
    partial_rebalance_weights,
    run_xsec_strategy,
)


def load_insider_events(insider_dir) -> pd.DataFrame:
    """(symbol, filed, value_signed, count_signed) from all quarterly zips."""
    parts = []
    for zp in sorted(insider_dir.glob("*_form345.zip")):
        try:
            z = zipfile.ZipFile(zp)
            names = {n.upper(): n for n in z.namelist()}
            sub = pd.read_csv(io.BytesIO(z.read(names["SUBMISSION.TSV"])),
                              sep="\t", low_memory=False,
                              usecols=["ACCESSION_NUMBER", "FILING_DATE",
                                       "ISSUERTRADINGSYMBOL"])
            tr = pd.read_csv(io.BytesIO(z.read(names["NONDERIV_TRANS.TSV"])),
                             sep="\t", low_memory=False,
                             usecols=["ACCESSION_NUMBER", "TRANS_CODE",
                                      "TRANS_SHARES", "TRANS_PRICEPERSHARE"])
        except Exception as e:
            print(f"  {zp.name}: {type(e).__name__} — skipped")
            continue
        tr = tr[tr["TRANS_CODE"].isin(["P", "S"])]
        m = tr.merge(sub, on="ACCESSION_NUMBER", how="left").dropna(
            subset=["ISSUERTRADINGSYMBOL", "FILING_DATE"])
        val = (pd.to_numeric(m["TRANS_SHARES"], errors="coerce")
               * pd.to_numeric(m["TRANS_PRICEPERSHARE"], errors="coerce"))
        sign = np.where(m["TRANS_CODE"] == "P", 1.0, -1.0)
        parts.append(pd.DataFrame({
            "symbol": m["ISSUERTRADINGSYMBOL"].str.upper().str.strip(),
            "filed": pd.to_datetime(m["FILING_DATE"], errors="coerce",
                                    format="mixed"),
            "value": (val.fillna(0.0) * sign).values,
            "count": sign,
        }))
    ev = pd.concat(parts, ignore_index=True).dropna(subset=["filed"])
    print(f"insider events: {len(ev):,} P/S transactions, "
          f"{ev['symbol'].nunique():,} symbols, "
          f"{ev['filed'].min():%Y-%m} -> {ev['filed'].max():%Y-%m}")
    return ev


def main() -> None:
    data_dir = config.REPORTS_DIR.parent / "data"
    prices = pd.read_parquet(data_dir / "broad_prices.parquet")
    prices.index = pd.to_datetime(prices.index)
    prices = prices.dropna(how="all")
    dollar_vol = pd.read_parquet(data_dir / "broad_volumes.parquet").reindex(prices.index)
    volumes = dollar_vol / prices
    returns = compute_returns(prices)

    ev = load_insider_events(data_dir / "insider")
    ev = ev[ev["symbol"].isin(prices.columns)]
    # daily signed panels on the price calendar (filed -> next trading day)
    val_p = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    cnt_p = val_p.copy()
    pos = prices.index.searchsorted(ev["filed"].values, side="right")
    keep = pos < len(prices.index)
    ev = ev[keep]; pos = pos[keep]
    for (i, col), v, c in zip(
            zip(pos, ev["symbol"].values), ev["value"].values, ev["count"].values):
        j = val_p.columns.get_loc(col)
        val_p.iat[i, j] += v
        cnt_p.iat[i, j] += c
    med_dv = dollar_vol.rolling(126, min_periods=42).median()
    extras = {
        "ins_netbuy_180": val_p.rolling(180).sum() / med_dv.where(med_dv > 0),
        "ins_buyers_180": cnt_p.rolling(180).sum(),
    }
    cov = extras["ins_buyers_180"].abs().gt(0).mean(axis=1)
    print(f"insider coverage (names with activity, 2013+): "
          f"{cov[cov.index >= '2013'].mean():.1%}")

    med_all = dollar_vol.median()
    cost_bps = pd.Series(
        np.where(med_all > 5e7, 5.0, np.where(med_all > 1e7, 10.0, 20.0)),
        index=prices.columns)

    rows = {}
    for name, kw, tau, ffl in [
        ("weekly", dict(horizon=5, rebal_every=1), 0.10, 7),
        ("monthly", dict(horizon=21, rebal_every=4), 0.25, 28),
    ]:
        print(f"Training {name} + insider features (broad panel)...")
        res = run_xsec_strategy(
            prices, volumes, membership=None, extra_features=extras,
            elig_kwargs=dict(min_price=5.0, min_dollar_vol=5e6,
                             min_history=252), **kw)
        ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
        print(f"  IC {res.ic.mean():+.4f} (t={ic_t:.2f}, n={len(res.ic)})")
        targets = res.predictions.apply(_decile_weights, axis=1, top_frac=0.10)
        held = partial_rebalance_weights(targets, tau)
        daily = held.reindex(prices.index).ffill(limit=ffl).fillna(0.0)
        bt = run_weights_backtest(daily, returns, cost_bps=cost_bps)
        oos = bt.portfolio.index >= res.predictions.index[0]
        s = summary_stats(bt.portfolio[oos])
        s["ic_mean"], s["ic_t"] = float(res.ic.mean()), ic_t
        rows[f"{name}_tau{tau:.2f}"] = s
        print(f"  net sharpe {s.get('sharpe'):.3f}")

    table = pd.DataFrame(rows).T
    table.to_csv(config.REPORTS_DIR / "cycle11_insider.csv")
    with pd.option_context("display.width", 200,
                           "display.float_format", "{:.4f}".format):
        print("\n=== Cycle 11: insider features, broad panel (UPPER BOUND) ===")
        print(table)


if __name__ == "__main__":
    main()
