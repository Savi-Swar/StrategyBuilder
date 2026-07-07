"""The technical board: the desk's original indicator toolkit (RSI,
Bollinger, MACD, golden cross, momentum — now joined by VWAP) computed
across the tradable universe as DESCRIPTIVE market state.

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
    "mom252": lambda v: v > 0,
}


def build_board(prices: pd.DataFrame, volumes: pd.DataFrame | None,
                universe: pd.DataFrame) -> pd.DataFrame:
    tradable = [t for t in prices.columns
                if t in universe.index and universe.at[t, "tradable"]]
    px = prices[tradable].ffill(limit=3)
    last = px.index[-1]

    ma20 = px.rolling(20, min_periods=20).mean()
    sd20 = px.rolling(20, min_periods=20).std()
    pctb = (px - (ma20 - 2 * sd20)) / (4 * sd20)

    ema12 = px.ewm(span=12, min_periods=12).mean()
    ema26 = px.ewm(span=26, min_periods=26).mean()
    macd = ema12 - ema26
    hist = macd - macd.ewm(span=9, min_periods=9).mean()

    sma50 = px.rolling(50, min_periods=50).mean()
    sma200 = px.rolling(200, min_periods=200).mean()

    vwap_dist = pd.Series(np.nan, index=tradable)
    if volumes is not None:
        vol = volumes.reindex(columns=tradable).reindex(px.index).fillna(0.0)
        pv = (px * vol).rolling(20, min_periods=10).sum()
        vv = vol.rolling(20, min_periods=10).sum()
        vwap = (pv / vv.replace(0.0, np.nan))
        vwap_dist = (px / vwap - 1.0).loc[last]

    board = pd.DataFrame({
        "asset_class": universe.loc[tradable, "asset_class"],
        "rsi14": rsi(px, 14).loc[last],
        "pctb": pctb.loc[last],
        "macd_bps": (hist.loc[last] / px.loc[last]) * 1e4,
        "golden": (sma50.loc[last] > sma200.loc[last]),
        "vwap_dist": vwap_dist,
        "mom252": px.pct_change(252, fill_method=None).loc[last],
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
