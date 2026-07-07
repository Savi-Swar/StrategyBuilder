"""Run every registered classic strategy through the engine, net of costs,
and report with multiple-testing accounting (Deflated Sharpe Ratio)."""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_backtest
from quark.backtest.metrics import deflated_sharpe, summary_stats
from quark.data.loader import compute_returns, load_prices
from quark.data.quality import clean_panel, quality_report
from quark.strategies.classic import N_TRIALS, STRATEGIES
from quark.universe import load_universe


def load_study1_panel():
    """Cleaned multi-asset price panel + universe. Headline excludes the
    hindsight-picked single stocks (NVDA et al. were chosen knowing how the
    story ended)."""
    uni = load_universe()
    prices = load_prices(tickers=list(uni.index))
    report = quality_report(prices)
    print(report.summary())
    return clean_panel(prices, report), uni


def main() -> None:
    prices, uni = load_study1_panel()
    headline_uni = uni[~uni["hindsight_picked"]]
    headline_px = prices[[t for t in prices.columns if t in headline_uni.index]]

    rows, daily = {}, {}
    for name, strat in STRATEGIES.items():
        signals = strat(headline_px)
        res = run_backtest(signals, headline_px, universe=headline_uni)
        rows[name] = res.stats
        daily[name] = res.portfolio

    table = pd.DataFrame(rows).T.sort_values("sharpe", ascending=False)

    # Multiple-testing accounting: the best Sharpe was selected from N_TRIALS
    # variants; deflate it against the expected max of that many null trials.
    best = table.index[0]
    sr_daily = pd.Series({k: v.mean() / v.std() for k, v in daily.items()})
    dsr = deflated_sharpe(daily[best], n_trials=N_TRIALS, sr_var=float(sr_daily.var()))

    # Robustness: best strategy at lag=2 (one extra day of execution delay)
    res_lag2 = run_backtest(STRATEGIES[best](headline_px), headline_px,
                            universe=headline_uni, lag=2)

    # Best strategy including the hindsight-picked stocks (with/without view)
    res_with = run_backtest(STRATEGIES[best](prices), prices, universe=uni)

    # Benchmark: buy-and-hold S&P 500 (price index; understates dividends)
    gspc = compute_returns(prices[["^GSPC"]])["^GSPC"]
    table.loc["buy_hold_GSPC"] = summary_stats(gspc)
    table.loc[f"{best}_lag2"] = res_lag2.stats
    table.loc[f"{best}_with_stocks"] = res_with.stats

    config.REPORTS_DIR.mkdir(exist_ok=True)
    table.to_csv(config.REPORTS_DIR / "baselines.csv")
    pd.concat(daily, axis=1).to_csv(config.REPORTS_DIR / "baseline_daily_returns.csv")

    with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
        print("\n=== Classic baselines, net of costs (headline universe) ===")
        print(table)
    print(f"\nBest variant: {best}")
    print(f"Deflated Sharpe: DSR={dsr['dsr']:.3f} "
          f"(daily SR {dsr['sr_daily']:.4f} vs expected-max-under-null "
          f"{dsr['sr_star_daily']:.4f}, N={dsr['n_trials']} trials)")
    if dsr["dsr"] < 0.95:
        print("=> Cannot reject that the best classic variant is a selection artifact.")


if __name__ == "__main__":
    main()
