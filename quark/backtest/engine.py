"""The backtest engine. Two modes:

- run_backtest: Study 1 — signal panels in [-1, 1], vol-targeted per
  instrument, equal-weight (i.e. inverse-vol) aggregation across the live
  universe. No optimizer by design: optimizing weights on in-sample Sharpes
  is the exact overfitting trap this project exists to avoid.
- run_weights_backtest: Study 2 — explicit portfolio weight panels
  (e.g. dollar-neutral decile weights), applied as-is.

Causality: positions = scaled_signals.shift(lag). With lag=1 a signal
computed on bar t earns returns from bar t+1 onward (trade at t's close,
market-on-close convention). The no-lookahead unit test in
tests/test_engine.py is the contract.
"""

from dataclasses import dataclass, field

import pandas as pd

from quark import config
from quark.backtest.costs import turnover_costs
from quark.backtest.metrics import summary_stats
from quark.backtest.sizing import vol_target_positions
from quark.data.loader import compute_returns


@dataclass
class BacktestResult:
    positions: pd.DataFrame
    gross_returns: pd.DataFrame
    costs: pd.DataFrame
    net_returns: pd.DataFrame
    portfolio: pd.Series
    equity: pd.Series
    turnover: pd.Series
    stats: dict = field(default_factory=dict)


def _finalize(positions, gross, costs, net, portfolio) -> BacktestResult:
    equity = (1.0 + portfolio).cumprod()
    turnover = positions.diff().abs().sum(axis=1)
    if len(turnover):
        turnover.iloc[0] = positions.iloc[0].abs().sum()
    stats = summary_stats(portfolio)
    n_years = max(len(portfolio) / config.ANN_FACTOR, 1e-9)
    stats["ann_turnover"] = float(turnover.sum() / n_years)
    stats["cost_drag_ann"] = float(costs.sum().sum() / n_years) if len(costs) else 0.0
    return BacktestResult(positions, gross, costs, net, portfolio, equity, turnover, stats)


def run_backtest(
    signals: pd.DataFrame,
    prices: pd.DataFrame,
    *,
    universe: pd.DataFrame,
    vol_target: float = config.VOL_TARGET,
    lookback: int = config.VOL_LOOKBACK,
    max_leverage: float = config.MAX_LEVERAGE,
    lag: int = config.EXECUTION_LAG,
) -> BacktestResult:
    if lag < 1:
        raise ValueError("lag must be >= 1; lag=0 is lookahead")

    tradable = [
        t for t in signals.columns
        if t in prices.columns and t in universe.index and universe.at[t, "tradable"]
    ]
    signals, prices = signals[tradable], prices[tradable]
    returns = compute_returns(prices)

    scaled = vol_target_positions(
        signals, returns, vol_target=vol_target,
        lookback=lookback, max_leverage=max_leverage,
    )
    positions = scaled.shift(lag).fillna(0.0)

    gross = positions * returns  # NaN return -> NaN PnL, treated as 0 below
    costs = turnover_costs(positions, universe.loc[tradable, "cost_bps"])
    net = gross.fillna(0.0) - costs

    # Divisor = instruments alive to date (first observation seen), not the
    # full panel width — otherwise early years are diluted by instruments
    # that don't exist yet (ETH starts 2017).
    alive = prices.notna().cummax(axis=0)
    n_alive = alive.sum(axis=1).clip(lower=1)
    portfolio = net.sum(axis=1) / n_alive

    return _finalize(positions, gross, costs, net, portfolio)


def run_weights_backtest(
    weights: pd.DataFrame,
    returns: pd.DataFrame,
    cost_bps: pd.Series | float,
    *,
    lag: int = config.EXECUTION_LAG,
) -> BacktestResult:
    """Backtest explicit portfolio weights (rows ~ dates, columns ~ tickers).
    Weights are interpreted as fractions of NAV; the caller owns neutrality
    and gross-exposure conventions."""
    if lag < 1:
        raise ValueError("lag must be >= 1; lag=0 is lookahead")
    weights, returns = weights.align(returns, join="inner")

    positions = weights.shift(lag).fillna(0.0)
    gross = positions * returns
    if not isinstance(cost_bps, pd.Series):
        cost_bps = pd.Series(float(cost_bps), index=positions.columns)
    costs = turnover_costs(positions, cost_bps)
    net = gross.fillna(0.0) - costs
    portfolio = net.sum(axis=1)

    return _finalize(positions, gross, costs, net, portfolio)
