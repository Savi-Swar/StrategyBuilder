"""Comparison tables rendered as markdown (no tabulate dependency)."""

import pandas as pd

from quark.backtest.metrics import summary_stats

DISPLAY_COLS = [
    "cagr", "ann_vol", "sharpe", "sortino", "max_dd", "calmar",
    "hit_rate", "skew",
]


def comparison_table(daily: dict[str, pd.Series]) -> pd.DataFrame:
    """Stats for each named daily-return series on their COMMON window."""
    idx = None
    for s in daily.values():
        idx = s.index if idx is None else idx.intersection(s.index)
    rows = {name: summary_stats(s.loc[idx]) for name, s in daily.items()}
    return pd.DataFrame(rows).T[DISPLAY_COLS]


def to_markdown(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    def fmt(v):
        return floatfmt.format(v) if isinstance(v, float) else str(v)

    header = "| | " + " | ".join(df.columns) + " |"
    sep = "|" + "---|" * (len(df.columns) + 1)
    lines = [header, sep]
    for name, row in df.iterrows():
        lines.append("| " + str(name) + " | " + " | ".join(fmt(v) for v in row) + " |")
    return "\n".join(lines)
