"""Study 1 ML run: walk-forward multi-asset timing model, with the two
questions any interviewer will ask answered in the output:
1. Does it survive a shuffled-label control? (leakage check)
2. Is it just re-learning momentum? (correlation + residual Sharpe)
"""

import numpy as np
import pandas as pd

from quark import config
from quark.backtest.engine import run_backtest
from quark.backtest.metrics import deflated_sharpe, summary_stats
from quark.ml.pipeline import run_ml_strategy
from quark.strategies.classic import N_TRIALS, STRATEGIES
from run_baselines import load_study1_panel


def main() -> None:
    prices, uni = load_study1_panel()
    headline_uni = uni[~uni["hindsight_picked"]]
    headline_px = prices[[t for t in prices.columns if t in headline_uni.index]]

    print("Training walk-forward ML model...")
    ml = run_ml_strategy(prices, uni)
    print("\nPer-fold OOS quality (base_rate = fraction of up-labels):")
    print(ml.fold_stats.to_string(index=False, float_format="{:.4f}".format))

    res_ml = run_backtest(ml.signals, headline_px, universe=headline_uni)

    print("\nShuffled-label control (must be ~0.5 AUC, ~0 Sharpe)...")
    ml_shuf = run_ml_strategy(prices, uni, shuffle_labels=True, compute_importance=False)
    res_shuf = run_backtest(ml_shuf.signals, headline_px, universe=headline_uni)
    shuf_auc = ml_shuf.fold_stats["auc"].mean()

    # Is the ML just momentum? Compare on the common OOS window.
    oos = res_ml.portfolio.index[res_ml.portfolio.index >= ml.signals.index[0]]
    base_daily = {
        name: run_backtest(strat(headline_px), headline_px,
                           universe=headline_uni).portfolio.loc[oos]
        for name, strat in STRATEGIES.items()
    }
    res_base = run_backtest(STRATEGIES["tsmom_252"](headline_px), headline_px,
                            universe=headline_uni)
    ml_r, base_r = res_ml.portfolio.loc[oos], res_base.portfolio.loc[oos]
    corr = float(ml_r.corr(base_r))
    beta = float(ml_r.cov(base_r) / base_r.var())
    resid_sharpe = summary_stats(ml_r - beta * base_r)["sharpe"]

    # DSR: the ML config is one more trial on top of the classic registry;
    # sr_var is the observed dispersion of daily SRs across ALL trials.
    trial_srs = [s.mean() / s.std() for s in base_daily.values()]
    trial_srs.append(float(ml_r.mean() / ml_r.std()))
    dsr = deflated_sharpe(ml_r, n_trials=N_TRIALS + 1,
                          sr_var=float(np.var(trial_srs, ddof=1)))

    table = pd.DataFrame(
        {
            "ml_oos": summary_stats(ml_r),
            "tsmom_252_oos": summary_stats(base_r),
            "ml_shuffled": summary_stats(res_shuf.portfolio.loc[oos]),
        }
    ).T
    table["ann_turnover"] = [res_ml.stats["ann_turnover"],
                             res_base.stats["ann_turnover"],
                             res_shuf.stats["ann_turnover"]]

    config.REPORTS_DIR.mkdir(exist_ok=True)
    ml.fold_stats.to_csv(config.REPORTS_DIR / "ml_fold_stats.csv", index=False)
    table.to_csv(config.REPORTS_DIR / "ml_results.csv")
    pd.concat({"ml": ml_r, "tsmom_252": base_r}, axis=1).to_csv(
        config.REPORTS_DIR / "ml_daily_returns.csv")
    if ml.importance is not None:
        ml.importance.to_csv(config.REPORTS_DIR / "ml_feature_importance.csv")

    with pd.option_context("display.width", 160, "display.float_format", "{:.3f}".format):
        print("\n=== Study 1 OOS comparison (net of costs, common window) ===")
        print(table)
        print("\nTop features (permutation importance, last fold):")
        print(ml.importance.head(8))
    print(f"\nMean fold AUC: {ml.fold_stats['auc'].mean():.4f} "
          f"| shuffled control AUC: {shuf_auc:.4f}")
    print(f"Corr(ML, tsmom_252) = {corr:.3f}; beta = {beta:.2f}; "
          f"residual Sharpe = {resid_sharpe:.3f}")
    print(f"DSR (N={N_TRIALS + 1} trials): {dsr['dsr']:.3f}")


if __name__ == "__main__":
    main()
