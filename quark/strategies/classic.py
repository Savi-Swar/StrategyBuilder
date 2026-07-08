"""Classic indicator strategies as pure signal functions.

Contract: f(prices) -> DataFrame of signals in [-1, 1], same shape as prices,
NaN wherever the indicator is undefined (warmup, missing data). NaN signals
become zero positions in the engine.

EVERY variant ever evaluated lives in STRATEGIES. The registry size is the
trial count fed to the Deflated Sharpe Ratio — evaluating a variant without
registering it is exactly the selection bias this project exists to kill.
"""

from functools import partial

import numpy as np
import pandas as pd


def tsmom(prices: pd.DataFrame, lookback: int = 252) -> pd.DataFrame:
    """Time-series momentum: sign of the trailing `lookback`-day return."""
    trailing = prices.pct_change(lookback, fill_method=None)
    return np.sign(trailing)


def ma_crossover(prices: pd.DataFrame, fast: int = 50, slow: int = 200) -> pd.DataFrame:
    ma_f = prices.rolling(fast, min_periods=fast).mean()
    ma_s = prices.rolling(slow, min_periods=slow).mean()
    return np.sign(ma_f - ma_s)


def rsi(prices: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Cutler's RSI (simple-MA of gains/losses). NOTE: charting platforms
    default to Wilder's recursive smoothing — values can differ by several
    points; the UI labels this variant explicitly."""
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(window, min_periods=window).mean()
    loss = (-delta.clip(upper=0)).rolling(window, min_periods=window).mean()
    rs = gain / loss.replace(0.0, np.nan)
    out = 100.0 - 100.0 / (1.0 + rs)
    out = out.where(loss != 0, 100.0)
    out = out.where((gain != 0) | (loss != 0), 50.0)  # flat window: neutral
    return out.where(gain.notna() & loss.notna())


def rsi_reversion(prices: pd.DataFrame, window: int = 14,
                  lo: float = 30.0, hi: float = 70.0) -> pd.DataFrame:
    ind = rsi(prices, window)
    sig = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    sig = sig.mask(ind < lo, 1.0).mask(ind > hi, -1.0)
    return sig.where(ind.notna())


def macd_signal(prices: pd.DataFrame, fast: int = 12, slow: int = 26,
                signal: int = 9) -> pd.DataFrame:
    ema_f = prices.ewm(span=fast, min_periods=fast).mean()
    ema_s = prices.ewm(span=slow, min_periods=slow).mean()
    macd = ema_f - ema_s
    sig_line = macd.ewm(span=signal, min_periods=signal).mean()
    return np.sign(macd - sig_line).where(prices.notna())


def bollinger_reversion(prices: pd.DataFrame, window: int = 20,
                        k: float = 2.0) -> pd.DataFrame:
    ma = prices.rolling(window, min_periods=window).mean()
    sd = prices.rolling(window, min_periods=window).std()
    upper, lower = ma + k * sd, ma - k * sd
    sig = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    sig = sig.mask(prices > upper, -1.0).mask(prices < lower, 1.0)
    return sig.where(ma.notna())


STRATEGIES: dict = {
    "tsmom_63": partial(tsmom, lookback=63),
    "tsmom_126": partial(tsmom, lookback=126),
    "tsmom_252": partial(tsmom, lookback=252),
    "ma_cross_50_200": partial(ma_crossover, fast=50, slow=200),
    "ma_cross_20_100": partial(ma_crossover, fast=20, slow=100),
    "rsi_rev_14": partial(rsi_reversion, window=14),
    "macd_12_26_9": partial(macd_signal),
    "boll_rev_20_2": partial(bollinger_reversion),
}

N_TRIALS = len(STRATEGIES)
