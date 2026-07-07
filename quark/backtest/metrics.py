"""Performance metrics, including the Deflated Sharpe Ratio.

Sharpe convention: rf = 0 throughout. Futures/FX positions are self-financing
so this is the right convention for them; the buy-and-hold equity benchmark
Sharpe is overstated by roughly the cash rate (noted in README).
"""

import numpy as np
import pandas as pd
from scipy import stats as sps

from quark import config

EULER_GAMMA = 0.5772156649015329


def max_drawdown(equity: pd.Series) -> float:
    """Max peak-to-trough drawdown of an EQUITY CURVE (not asset prices)."""
    return float((equity / equity.cummax() - 1.0).min())


def summary_stats(returns: pd.Series, ann: int = config.ANN_FACTOR) -> dict:
    r = returns.dropna()
    if r.empty or r.std() == 0:
        return {k: np.nan for k in (
            "cagr", "ann_vol", "sharpe", "sortino", "max_dd", "calmar",
            "hit_rate", "skew", "n_days")}
    equity = (1.0 + r).cumprod()
    years = len(r) / ann
    cagr = float(equity.iloc[-1] ** (1.0 / years) - 1.0)
    ann_vol = float(r.std() * np.sqrt(ann))
    sharpe = float(r.mean() / r.std() * np.sqrt(ann))
    downside = r[r < 0].std()
    sortino = float(r.mean() * ann / (downside * np.sqrt(ann))) if downside > 0 else np.nan
    mdd = max_drawdown(equity)
    active = r[r != 0]
    return {
        "cagr": cagr,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd": mdd,
        "calmar": float(cagr / abs(mdd)) if mdd < 0 else np.nan,
        "hit_rate": float((active > 0).mean()) if len(active) else np.nan,
        "skew": float(r.skew()),
        "n_days": int(len(r)),
    }


def probabilistic_sharpe(
    sr: float, n_obs: int, skew: float, kurt: float, sr_benchmark: float = 0.0
) -> float:
    """PSR (Bailey & Lopez de Prado 2012): P[true SR > sr_benchmark].

    All Sharpe ratios here are PER-PERIOD (e.g. daily), not annualized.
    `kurt` is non-excess kurtosis (normal = 3).
    """
    denom = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    z = (sr - sr_benchmark) * np.sqrt(n_obs - 1.0) / denom
    return float(sps.norm.cdf(z))


def expected_max_sharpe(n_trials: int, sr_var: float) -> float:
    """E[max SR] across `n_trials` zero-skill strategies whose estimated SRs
    have variance `sr_var` (per-period units)."""
    if n_trials <= 1 or sr_var <= 0:
        return 0.0
    return float(
        np.sqrt(sr_var)
        * ((1.0 - EULER_GAMMA) * sps.norm.ppf(1.0 - 1.0 / n_trials)
           + EULER_GAMMA * sps.norm.ppf(1.0 - 1.0 / (n_trials * np.e)))
    )


def deflated_sharpe(returns: pd.Series, n_trials: int, sr_var: float) -> dict:
    """DSR: PSR of the observed track record against the expected max SR of
    `n_trials` skill-less strategies. The honest question: 'given how many
    things we tried, how surprising is the best one?'"""
    r = returns.dropna()
    sr = float(r.mean() / r.std())  # per-period
    sr_star = expected_max_sharpe(n_trials, sr_var)
    dsr = probabilistic_sharpe(
        sr, len(r), float(r.skew()), float(r.kurt() + 3.0), sr_benchmark=sr_star
    )
    return {"sr_daily": sr, "sr_star_daily": sr_star, "n_trials": n_trials, "dsr": dsr}
