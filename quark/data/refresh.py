"""Data refresh from Yahoo Finance.

Refresh policy is FULL REPLACE per ticker: yfinance's auto-adjusted closes are
adjusted as-of the fetch date, so appending fresh rows to rows fetched years
ago would create level breaks around any dividend/split since the old fetch.
Re-downloading full history per ticker sidesteps this entirely.

Downloads are batched (one request per chunk of tickers) — per-ticker requests
trip Yahoo's rate limiter.
"""

import io
import sqlite3
import time
import urllib.request

import pandas as pd
import yfinance as yf

from quark import config

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
START = "2004-01-01"
CHUNK_SIZE = 40


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS stocks (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               ticker TEXT, date TEXT,
               open REAL, high REAL, low REAL, close REAL, volume INTEGER)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sp500_members (
               ticker TEXT PRIMARY KEY, name TEXT, sector TEXT)"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_stocks_ticker ON stocks(ticker)")


def _store_frame(conn: sqlite3.Connection, ticker: str, df: pd.DataFrame) -> int:
    """Replace all rows for `ticker` with the freshly downloaded frame.
    The DELETE only happens once we hold non-empty fresh data."""
    df = df.dropna(subset=["Close"])
    if df.empty:
        return 0
    rows = [
        (
            ticker,
            idx.strftime("%Y-%m-%d"),
            float(r["Open"]),
            float(r["High"]),
            float(r["Low"]),
            float(r["Close"]),
            int(r["Volume"]) if pd.notna(r["Volume"]) else 0,
        )
        for idx, r in df.iterrows()
    ]
    conn.execute("DELETE FROM stocks WHERE ticker = ?", (ticker,))
    conn.executemany(
        "INSERT INTO stocks (ticker, date, open, high, low, close, volume)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def refresh_tickers(
    tickers: list[str],
    db_path=None,
    start: str = START,
    chunk_size: int = CHUNK_SIZE,
) -> pd.DataFrame:
    """Batch-download full history for `tickers` and replace their DB rows.
    Returns a fetch report (ticker, n_rows, status)."""
    db_path = str(db_path or config.DB_PATH)
    report = []
    with sqlite3.connect(db_path) as conn:
        _ensure_tables(conn)
        for lo in range(0, len(tickers), chunk_size):
            chunk = tickers[lo : lo + chunk_size]
            try:
                data = yf.download(
                    chunk, start=start, auto_adjust=True,
                    group_by="ticker", progress=False, threads=True,
                )
            except Exception as exc:  # noqa: BLE001 — isolate chunk failures
                report.extend((t, 0, f"ERROR: {exc}") for t in chunk)
                continue
            for ticker in chunk:
                try:
                    df = data[ticker] if len(chunk) > 1 else data
                    n = _store_frame(conn, ticker, df)
                    report.append((ticker, n, "ok" if n else "EMPTY"))
                except (KeyError, ValueError) as exc:
                    report.append((ticker, 0, f"ERROR: {exc}"))
            time.sleep(1.0)  # stay polite with Yahoo between chunks
    rep = pd.DataFrame(report, columns=["ticker", "n_rows", "status"])
    print(rep["status"].value_counts().to_string())
    bad = rep[rep["status"] != "ok"]
    if not bad.empty:
        print("Non-ok fetches:\n", bad.to_string(index=False))
    return rep


def get_sp500_members() -> pd.DataFrame:
    """Current S&P 500 membership from Wikipedia. NOTE: current members only —
    this induces survivorship bias, documented in RESEARCH_NOTES.md."""
    req = urllib.request.Request(WIKI_SP500, headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
    tables = pd.read_html(io.StringIO(html))
    members = tables[0][["Symbol", "Security", "GICS Sector"]].copy()
    members.columns = ["ticker", "name", "sector"]
    # Yahoo uses dashes where the index uses dots (BRK.B -> BRK-B)
    members["ticker"] = members["ticker"].str.replace(".", "-", regex=False)
    return members


def fetch_sp500_universe(db_path=None, start: str = "2005-01-01") -> pd.DataFrame:
    """Fetch daily adjusted OHLCV for all current S&P 500 members and store
    membership + prices. Returns the fetch report."""
    db_path = str(db_path or config.DB_PATH)
    members = get_sp500_members()
    with sqlite3.connect(db_path) as conn:
        _ensure_tables(conn)
        conn.execute("DELETE FROM sp500_members")
        conn.executemany(
            "INSERT INTO sp500_members (ticker, name, sector) VALUES (?, ?, ?)",
            members.itertuples(index=False),
        )
        conn.commit()
    print(f"S&P 500 membership: {len(members)} tickers")
    return refresh_tickers(list(members["ticker"]), db_path=db_path, start=start)


def load_sp500_tickers(db_path=None) -> list[str]:
    db_path = str(db_path or config.DB_PATH)
    with sqlite3.connect(db_path) as conn:
        return [t for (t,) in conn.execute("SELECT ticker FROM sp500_members ORDER BY ticker")]


def load_sp500_sectors(db_path=None) -> dict[str, str]:
    """ticker -> GICS sector, from the stored membership table."""
    db_path = str(db_path or config.DB_PATH)
    with sqlite3.connect(db_path) as conn:
        return dict(conn.execute("SELECT ticker, sector FROM sp500_members"))


def load_sp500_names(db_path=None) -> dict[str, str]:
    """ticker -> company name, from the stored membership table."""
    db_path = str(db_path or config.DB_PATH)
    with sqlite3.connect(db_path) as conn:
        return dict(conn.execute("SELECT ticker, name FROM sp500_members"))
