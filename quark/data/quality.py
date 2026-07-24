"""Data-quality checks. The report is a first-class deliverable: its summary
is printed by every run script and its findings go in RESEARCH_NOTES.md."""

import sqlite3
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from quark import config
from quark.data.loader import compute_returns


@dataclass
class QualityReport:
    gaps: pd.DataFrame          # ticker, gap_start, gap_end, n_bdays
    stale_runs: pd.DataFrame    # ticker, start, end, length
    spikes: pd.DataFrame        # ticker, date, price, ret, reason
    short_history: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"gaps: {len(self.gaps)}",
            f"stale runs: {len(self.stale_runs)}",
            f"spike/nonpositive flags: {len(self.spikes)}",
            f"short history (<252 obs): {self.short_history}",
        ]
        return "QualityReport(" + "; ".join(lines) + ")"


def count_db_duplicates(db_path=None) -> int:
    """Duplicate (ticker, date) rows currently in the DB (loader drops them)."""
    db_path = str(db_path or config.DB_PATH)
    with sqlite3.connect(db_path) as conn:
        (n,) = conn.execute(
            """SELECT COALESCE(SUM(c - 1), 0) FROM
               (SELECT COUNT(*) AS c FROM stocks GROUP BY ticker, date HAVING c > 1)"""
        ).fetchone()
    return int(n)


def quality_report(
    prices: pd.DataFrame,
    max_gap_bdays: int = 5,
    stale_len: int = 5,
    spike_thresh: float = 0.5,
    min_history: int = 252,
) -> QualityReport:
    returns = compute_returns(prices)
    gaps, stales, spikes = [], [], []

    for ticker in prices.columns:
        s = prices[ticker].dropna()
        if s.empty:
            continue
        # Gaps: business days between consecutive observations
        obs = s.index.to_series()
        delta = obs.diff()
        for prev, cur in zip(obs[:-1][delta[1:].gt(pd.Timedelta(days=1)).values],
                             obs[1:][delta[1:].gt(pd.Timedelta(days=1)).values]):
            n_bd = len(pd.bdate_range(prev, cur)) - 2  # missing bdays strictly between
            if n_bd > max_gap_bdays:
                gaps.append((ticker, prev, cur, n_bd))
        # Stale runs: >= stale_len identical consecutive closes
        run_id = (s != s.shift()).cumsum()
        run_sizes = s.groupby(run_id).size()
        for rid in run_sizes[run_sizes >= stale_len].index:
            idx = s.index[run_id == rid]
            stales.append((ticker, idx[0], idx[-1], len(idx)))
        # Spikes and non-positive prices
        bad_px = s[s <= 0]
        for dt, px in bad_px.items():
            spikes.append((ticker, dt, px, np.nan, "price<=0"))
        r = returns[ticker]
        big = r[r.abs() > spike_thresh]
        for dt, ret in big.items():
            spikes.append((ticker, dt, prices.at[dt, ticker], ret, f"|ret|>{spike_thresh}"))

    short = [t for t in prices.columns if prices[t].notna().sum() < min_history]
    return QualityReport(
        gaps=pd.DataFrame(gaps, columns=["ticker", "gap_start", "gap_end", "n_bdays"]),
        stale_runs=pd.DataFrame(stales, columns=["ticker", "start", "end", "length"]),
        spikes=pd.DataFrame(spikes, columns=["ticker", "date", "price", "ret", "reason"]),
        short_history=short,
    )


def clean_panel(prices: pd.DataFrame, report: QualityReport | None = None) -> pd.DataFrame:
    """NaN-out flagged prices. Both return legs touching a flagged bar die,
    which is intended: a return into or out of a corrupt print is corrupt.
    Covers the CL=F negative-price episode (2020-04) among others."""
    if report is None:
        report = quality_report(prices)
    out = prices.copy()
    out[out <= 0] = np.nan
    for _, row in report.spikes.iterrows():
        out.at[row["date"], row["ticker"]] = np.nan
    # Post-condition: a cleaned panel must satisfy the panel contract
    # (no nonpositive prices, no identity-break return spikes). If this
    # raises, the cleaning rules above have drifted out of sync with the
    # contract — fix the rule, don't loosen the contract.
    from quark.data.contracts import validate_price_panel
    return validate_price_panel(out)
