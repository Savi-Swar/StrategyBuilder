"""The technical board: the desk's original indicator toolkit (RSI,
Bollinger, MACD, golden cross, momentum — now joined by VWAP) computed
across the tradable universe as DESCRIPTIVE market state.

Two horizons:
- "tactical": daily bars — RSI14, %B(20d), MACD(12,26,9), 50/200d cross,
  VWAP20d, 12-month momentum.
- "position": weekly bars (the 6-month lens) — RSI14w, %B(20w),
  MACD(12,26,9 weekly), the classic 10/40-week cross, VWAP20w,
  6-month (26-week) momentum.

Honesty contract: these are the exact indicators Study 1 backtested; net of
costs none cleared the Deflated Sharpe bar as standalone strategies. They
are shown as a read of the tape, not as trade signals — the consensus score
is a summary of agreement, not an edge.
"""

import numpy as np
import pandas as pd

from quark.strategies.classic import rsi

BULL_RULES = {  # column -> is-bullish predicate, conventional trend reading
    "rsi14": lambda v: v > 50,
    "pctb": lambda v: v > 0.5,
    "macd_bps": lambda v: v > 0,
    "golden": lambda v: bool(v),
    "vwap_dist": lambda v: v > 0,
    "mom": lambda v: v > 0,
}

MODES = {
    "tactical": {"resample": None, "boll": 20, "fast_ma": 50, "slow_ma": 200,
                 "vwap": 20, "mom": 252},
    "position": {"resample": "W-FRI", "boll": 20, "fast_ma": 10, "slow_ma": 40,
                 "vwap": 20, "mom": 26},
}


def build_board(prices: pd.DataFrame, volumes: pd.DataFrame | None,
                universe: pd.DataFrame, mode: str = "tactical") -> pd.DataFrame:
    p = MODES[mode]
    tradable = [t for t in prices.columns
                if t in universe.index and universe.at[t, "tradable"]]
    px = prices[tradable].ffill(limit=3)
    vol = (volumes.reindex(columns=tradable).reindex(px.index).fillna(0.0)
           if volumes is not None else None)
    if p["resample"]:
        px = px.resample(p["resample"]).last()
        if vol is not None:
            vol = vol.resample(p["resample"]).sum()
    last = px.index[-1]

    ma = px.rolling(p["boll"], min_periods=p["boll"]).mean()
    sd = px.rolling(p["boll"], min_periods=p["boll"]).std()
    pctb = (px - (ma - 2 * sd)) / (4 * sd)

    ema12 = px.ewm(span=12, min_periods=12).mean()
    ema26 = px.ewm(span=26, min_periods=26).mean()
    macd = ema12 - ema26
    hist = macd - macd.ewm(span=9, min_periods=9).mean()

    fast = px.rolling(p["fast_ma"], min_periods=p["fast_ma"]).mean()
    slow = px.rolling(p["slow_ma"], min_periods=p["slow_ma"]).mean()

    vwap_dist = pd.Series(np.nan, index=tradable)
    if vol is not None:
        pv = (px * vol).rolling(p["vwap"], min_periods=p["vwap"] // 2).sum()
        vv = vol.rolling(p["vwap"], min_periods=p["vwap"] // 2).sum()
        vwap_dist = (px / (pv / vv.replace(0.0, np.nan)) - 1.0).loc[last]

    board = pd.DataFrame({
        "asset_class": universe.loc[tradable, "asset_class"],
        "rsi14": rsi(px, 14).loc[last],
        "pctb": pctb.loc[last],
        "macd_bps": (hist.loc[last] / px.loc[last]) * 1e4,
        "golden": (fast.loc[last] > slow.loc[last]),
        "vwap_dist": vwap_dist,
        "mom": px.pct_change(p["mom"], fill_method=None).loc[last],
    })
    board = board.dropna(subset=["rsi14", "pctb"])

    def consensus(row) -> int:
        score = 0
        for col, rule in BULL_RULES.items():
            v = row[col]
            if pd.isna(v):
                continue
            score += 1 if rule(v) else -1
        return score

    board["consensus"] = board.apply(consensus, axis=1)
    return board.sort_values("consensus", ascending=False)
