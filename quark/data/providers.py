"""Second data sources — not to replace Yahoo (nothing free matches its
breadth) but to CROSS-VERIFY it. Single-source data risk is real: the daily
job compares recent returns for a sample of names against an independent
provider and surfaces a trust tile. Disagreement is compared on RETURNS, not
closes (providers differ on dividend adjustment; returns only diverge
materially on bad prints).

- Tiingo: the primary verifier — activates when TIINGO_API_KEY is set
  (free account at tiingo.com); clean adjusted closes, paid upgrade path.
- Stooq: keyless fallback ('<ticker>.us') — NOTE: as of 2026-07 stooq
  bot-walls the CSV endpoint from many networks; the fetch degrades to None
  and the trust tile reports the check as inactive rather than lying.
"""

import io
import os
import urllib.request

import numpy as np
import pandas as pd

TOL_BPS = 50          # a daily-return disagreement beyond this is a flag
MAX_BAD_DAYS = 2      # tolerated big-diff days per ticker (ex-div timing)


def _http(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "vig/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def fetch_stooq_close(ticker: str) -> pd.Series | None:
    """Daily closes from Stooq (US equities only; keyless)."""
    if any(x in ticker for x in ("=", "^", "-USD", ".")):
        return None
    try:
        raw = _http(f"https://stooq.com/q/d/l/?s={ticker.lower()}.us&i=d")
        df = pd.read_csv(io.StringIO(raw))
        if "Close" not in df.columns or df.empty:
            return None
        s = pd.Series(df["Close"].values,
                      index=pd.to_datetime(df["Date"]), name=ticker)
        return s.dropna()
    except Exception:  # noqa: BLE001 — verification is best-effort
        return None


def fetch_tiingo_close(ticker: str, api_key: str | None = None) -> pd.Series | None:
    """Adjusted daily closes from Tiingo (free API key required)."""
    api_key = api_key or os.environ.get("TIINGO_API_KEY")
    if not api_key or any(x in ticker for x in ("=", "^", "-USD")):
        return None
    try:
        import json
        raw = _http("https://api.tiingo.com/tiingo/daily/"
                    f"{ticker}/prices?startDate=2024-01-01&token={api_key}")
        rows = json.loads(raw)
        if not rows:
            return None
        s = pd.Series({pd.Timestamp(r["date"][:10]): r["adjClose"]
                       for r in rows}, name=ticker)
        return s.dropna()
    except Exception:  # noqa: BLE001
        return None


def cross_verify(prices: pd.DataFrame, tickers: list[str],
                 days: int = 60) -> pd.DataFrame:
    """Compare recent daily returns per ticker against an independent source.
    Prefers Tiingo when a key is present, else Stooq. Returns one row per
    checked ticker: n_days, median/max abs diff (bps), bad_days, status."""
    use_tiingo = bool(os.environ.get("TIINGO_API_KEY"))
    rows = []
    for t in tickers:
        alt = (fetch_tiingo_close(t) if use_tiingo else None) or fetch_stooq_close(t)
        if alt is None or t not in prices.columns:
            continue
        ours = prices[t].dropna().tail(days)
        both = pd.concat({"y": ours, "a": alt}, axis=1).dropna().tail(days)
        if len(both) < 20:
            rows.append({"ticker": t, "n_days": len(both), "median_bps": np.nan,
                         "max_bps": np.nan, "bad_days": np.nan,
                         "status": "insufficient", "source": "tiingo" if use_tiingo else "stooq"})
            continue
        ry, ra = both["y"].pct_change().dropna(), both["a"].pct_change().dropna()
        diff = (ry - ra).abs() * 1e4
        bad = int((diff > TOL_BPS).sum())
        rows.append({
            "ticker": t, "n_days": len(diff),
            "median_bps": round(float(diff.median()), 1),
            "max_bps": round(float(diff.max()), 1),
            "bad_days": bad,
            "status": "ok" if bad <= MAX_BAD_DAYS else "FLAG",
            "source": "tiingo" if use_tiingo else "stooq",
        })
    return pd.DataFrame(rows)


def verification_summary(report: pd.DataFrame) -> dict:
    if report is None or report.empty:
        return {}
    checked = report[report["status"] != "insufficient"]
    flagged = checked[checked["status"] == "FLAG"]
    return {
        "source": report["source"].iloc[0],
        "n_checked": int(len(checked)),
        "n_flagged": int(len(flagged)),
        "flagged": list(flagged["ticker"]),
        "status": ("green" if len(flagged) == 0 else
                   "yellow" if len(flagged) <= 2 else "red"),
    }
