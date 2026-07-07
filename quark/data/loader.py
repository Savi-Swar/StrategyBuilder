"""Load price panels from SQLite into tidy date x ticker DataFrames."""

import sqlite3

import pandas as pd

from quark import config


def load_prices(
    db_path=None,
    tickers: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Close-price panel (DatetimeIndex business days x ticker columns).

    - Duplicate (ticker, date) rows are dropped keeping the last insert.
    - The index is a business-day calendar spanning the data. Weekend crypto
      bars are dropped; a Monday crypto return therefore spans the actual
      Fri->Mon move. Market holidays remain NaN for the markets that were
      closed — they must NOT be forward-filled (see compute_returns).
    - Leading NaNs before an instrument's first observation are preserved.
    """
    db_path = str(db_path or config.DB_PATH)
    query = "SELECT ticker, date, close FROM stocks"
    params: list = []
    clauses = []
    if tickers is not None:
        clauses.append(f"ticker IN ({','.join('?' * len(tickers))})")
        params.extend(tickers)
    if start is not None:
        clauses.append("date >= ?")
        params.append(str(start))
    if end is not None:
        clauses.append("date <= ?")
        params.append(str(end))
    if clauses:
        query += " WHERE " + " AND ".join(clauses)

    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql(query, conn, params=params or None)

    df["date"] = pd.to_datetime(df["date"], format="mixed").dt.normalize()
    df = df.drop_duplicates(subset=["ticker", "date"], keep="last")
    panel = df.pivot(index="date", columns="ticker", values="close").sort_index()
    bdays = pd.bdate_range(panel.index.min(), panel.index.max())
    return panel.reindex(bdays)


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Simple returns. ``fill_method=None`` is load-bearing: pad-filling
    across gaps would manufacture phantom 0% returns off stale prices."""
    return prices.pct_change(fill_method=None)
