"""Study 2 run: cross-sectional long-short equity with IC analysis,
decile monotonicity, and a shuffled-label control."""

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


def main() -> None:
    tickers = load_sp500_tickers()
    print(f"Equity universe: {len(tickers)} current S&P 500 members "
          "(survivorship-biased by construction — see RESEARCH_NOTES.md)")
    prices = load_prices(tickers=tickers, start="2005-01-01")
    volumes = load_prices(tickers=tickers, start="2005-01-01", field="volume")
    report = quality_report(prices)
    print(report.summary())
    prices = clean_panel(prices, report)
    # Equity-only panel: an all-NaN row is a US market holiday, not data —
    # drop it so the calendar is actual NYSE trading days.
    prices = prices.dropna(how="all")
    volumes = volumes.reindex(prices.index)
    returns = compute_returns(prices)

    # TRIAL ACCOUNTING: two pre-declared configs, both always reported.
    print("Training walk-forward cross-sectional model (h=5, weekly)...")
    res = run_xsec_strategy(prices, volumes, horizon=5, rebal_every=1)
    bt = run_weights_backtest(res.weights, returns, cost_bps=EQUITY_COST_BPS)

    print("Secondary config (h=21, monthly rebalance)...")
    res_m = run_xsec_strategy(prices, volumes, horizon=21, rebal_every=4)
    bt_m = run_weights_backtest(res_m.weights, returns, cost_bps=EQUITY_COST_BPS)

    print("Shuffled-label control (primary config)...")
    res_shuf = run_xsec_strategy(prices, volumes, shuffle_labels=True)
    bt_shuf = run_weights_backtest(res_shuf.weights, returns, cost_bps=EQUITY_COST_BPS)

    oos = bt.portfolio.index[bt.portfolio.index >= res.predictions.index[0]]
    ls_r, shuf_r = bt.portfolio.loc[oos], bt_shuf.portfolio.loc[oos]
    ls_m = bt_m.portfolio.loc[oos]

    ic_mean = float(res.ic.mean())
    ic_tstat = float(res.ic.mean() / res.ic.std() * np.sqrt(len(res.ic)))
    icm_tstat = float(res_m.ic.mean() / res_m.ic.std() * np.sqrt(len(res_m.ic)))

    table = pd.DataFrame(
        {
            "ls_weekly_h5_net": summary_stats(ls_r),
            "ls_monthly_h21_net": summary_stats(ls_m),
            "shuffled_control": summary_stats(shuf_r),
        }
    ).T
    # annualize turnover over the OOS window (engine stats span the full
    # panel, where weights are zero pre-2012 — diluting by ~1.48x)
    def _oos_turnover(b):
        m = b.portfolio.index.isin(oos)
        return float(b.turnover[m].sum() / (m.sum() / config.ANN_FACTOR))

    table["ann_turnover"] = [_oos_turnover(bt), _oos_turnover(bt_m),
                             _oos_turnover(bt_shuf)]

    config.REPORTS_DIR.mkdir(exist_ok=True)
    res.fold_stats.to_csv(config.REPORTS_DIR / "xsec_fold_stats.csv", index=False)
    table.to_csv(config.REPORTS_DIR / "xsec_results.csv")
    res.ic.to_csv(config.REPORTS_DIR / "xsec_ic_series.csv")
    res.decile_means.to_csv(config.REPORTS_DIR / "xsec_decile_means.csv")
    ls_r.to_csv(config.REPORTS_DIR / "xsec_daily_returns.csv")

    with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
        print("\nPer-fold OOS quality:")
        print(res.fold_stats.to_string(index=False, float_format="{:.4f}".format))
        print("\n=== Study 2: dollar-neutral L/S deciles, net of costs ===")
        print(table)
        print("\nMean gross 5d fwd return by prediction decile (should be monotonic):")
        print((res.decile_means * 1e4).round(1).to_string())
    print(f"\nIC (h=5 weekly):   mean={ic_mean:.4f}, t-stat={ic_tstat:.2f}, "
          f"n={len(res.ic)} weeks")
    print(f"IC (h=21 monthly): mean={res_m.ic.mean():.4f}, t-stat={icm_tstat:.2f}, "
          f"n={len(res_m.ic)} months")
    print(f"Shuffled control: mean fold AUC {res_shuf.fold_stats['auc'].mean():.4f}, "
          f"IC {res_shuf.ic.mean():.4f}")
    print("Trial count for this study: 2 configs, both reported above.")


if __name__ == "__main__":
    main()
