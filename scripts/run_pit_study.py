"""Point-in-time universe study: how much of Study 2 is survivorship bias?

Two runs of the identical pipeline (h=5, weekly, purged walk-forward):
  current_members — today's S&P 500 list backfilled through history
                    (the shipped Study 2 config; upward-biased by design)
  pit_bestEffort  — Wikipedia-reconstructed membership: a name is eligible
                    only in months it was actually in the index, and removed
                    names with recoverable Yahoo history rejoin the panel

The PIT run is best-effort, not CRSP: Wikipedia's changes table is
"selected" changes, and Yahoo drops most delisted tickers, so the recovered
panel still under-represents the worst outcomes (bankruptcies delist AND
vanish from Yahoo). Direction of the remaining bias: PIT numbers here are
still optimistic. See RESEARCH_NOTES.md.
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_weights_backtest
from quark.backtest.metrics import summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.data.refresh import load_sp500_tickers
from quark.ml.xsec import run_xsec_strategy
from quark.universe import EQUITY_COST_BPS


def _prep(tickers: list[str]):
    prices = load_prices(tickers=tickers, start="2005-01-01")
    volumes = load_prices(tickers=tickers, start="2005-01-01", field="volume")
    prices = clean_panel(prices, quality_report(prices)).dropna(how="all")
    volumes = volumes.reindex(prices.index)
    return prices, volumes


def _evaluate(name, prices, volumes, membership=None) -> pd.Series:
    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1,
                            membership=membership)
    returns = compute_returns(prices)
    bt = run_weights_backtest(res.weights, returns, cost_bps=EQUITY_COST_BPS)
    r = bt.portfolio[bt.portfolio.index >= res.predictions.index[0]]
    s = summary_stats(r)
    ic_t = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    row = pd.Series({
        "ic_mean": float(res.ic.mean()), "ic_t": ic_t, "n_weeks": len(res.ic),
        "decile10_bps": float(res.decile_means.loc[10.0] * 1e4),
        "decile1_bps": float(res.decile_means.loc[1.0] * 1e4),
        "spread_bps": float((res.decile_means.loc[10.0]
                             - res.decile_means.loc[1.0]) * 1e4),
        "net_sharpe": s["sharpe"], "net_cagr": s["cagr"],
        "names_per_week": float(res.predictions.notna().sum(axis=1).median()),
    }, name=name)
    print(f"{name:<18} IC {row['ic_mean']:+.4f} (t={row['ic_t']:.2f})  "
          f"D10-D1 {row['spread_bps']:.0f} bps  "
          f"net Sharpe {row['net_sharpe']:+.2f}  "
          f"names/wk {row['names_per_week']:.0f}")
    return row


def main() -> None:
    pit = pd.read_csv(config.REPORTS_DIR / "pit_membership.csv",
                      parse_dates=["month_end"])
    mask = (pit.assign(v=1.0)
            .pivot(index="month_end", columns="ticker", values="v")
            .notna())

    print("Run 1/2: current members (shipped Study 2 config)...")
    cur_prices, cur_vols = _prep(load_sp500_tickers())
    rows = [_evaluate("current_members", cur_prices, cur_vols)]

    print("Run 2/2: best-effort point-in-time membership...")
    pit_prices, pit_vols = _prep(sorted(mask.columns))
    have = pit_prices.columns
    print(f"  PIT panel: {len(have)}/{mask.shape[1]} ever-member names have "
          "price data (the gap IS the survivorship hole)")
    rows.append(_evaluate("pit_bestEffort", pit_prices, pit_vols,
                          membership=mask[have]))

    table = pd.DataFrame(rows)
    out = config.REPORTS_DIR / "pit_study.csv"
    table.to_csv(out)
    print(f"\nWrote {out}")
    print(table.to_string(float_format=lambda v: f"{v: .4f}"))


if __name__ == "__main__":
    main()
