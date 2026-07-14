"""Event alerts, the Sunday digest, and daily state backup.

Alerts fire only on CHANGES (gate flips, new data flags) — the daily
top-trades notification already covers the routine. State is persisted in
reports/state.json between runs; small run artifacts are git-committed so
the ledger and briefs are versioned automatically.
"""

import json
import subprocess
from datetime import date

import pandas as pd

from quark import config

STATE_PATH = config.REPORTS_DIR / "state.json"


def _snapshot(result: dict) -> dict:
    h = result.get("health", {})
    return {
        "date": str(date.today()),
        "model_status": h.get("model_status"),
        "ic_mean": h.get("ic_mean"),
        "data_flags": sorted(result.get("data_check", {}).get("flagged", [])),
        "top": [f"{t['side']} {t['ticker']}" for t in result.get("trades", [])],
    }


def diff_events(prev: dict, cur: dict) -> list[str]:
    events = []
    ps, cs = prev.get("model_status"), cur.get("model_status")
    if ps and cs and ps != cs:
        sev = "⚠️" if cs in ("yellow", "red") else "✓"
        events.append(f"{sev} trust gate {ps} → {cs} "
                      f"(26w IC {cur.get('ic_mean', float('nan')):+.3f})")
    new_flags = set(cur.get("data_flags", [])) - set(prev.get("data_flags", []))
    if new_flags:
        events.append("⚠️ data cross-check flagged: " + ", ".join(sorted(new_flags)))
    return events


def notify(title: str, msg: str) -> None:
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{msg}" with title "{title}"'],
                       check=False, capture_output=True, timeout=10)
    except Exception:  # noqa: BLE001 — notifications are garnish
        pass


def run_alerts(result: dict) -> list[str]:
    prev = {}
    if STATE_PATH.exists():
        try:
            prev = json.loads(STATE_PATH.read_text())
        except json.JSONDecodeError:
            prev = {}
    cur = _snapshot(result)
    events = diff_events(prev, cur)
    for e in events[:3]:
        notify("Vig — alert", e)
    STATE_PATH.write_text(json.dumps(cur))
    return events


def weekly_digest(result: dict) -> str | None:
    """Sunday only: the week in one markdown file + a notification."""
    if date.today().weekday() != 6:
        return None
    h = result.get("health", {})
    review = result.get("review", {})
    trades = review.get("trades")
    lines = [f"# Vig — week ending {date.today().isoformat()}", ""]
    lines.append(f"**Trust gate:** {h.get('model_status', '?')} — "
                 f"{h.get('model_detail', '')}")
    if trades is not None and not trades.empty:
        recent = trades[trades["as_of"] >=
                        pd.Timestamp(date.today()) - pd.Timedelta(days=28)]
        if not recent.empty:
            hit = recent["win_rel"].mean()
            lines += ["", f"**Model calls, trailing 4 weeks:** "
                      f"{len(recent)} graded, hit {hit:.0%} vs S&P median, "
                      f"avg {recent['rel_5d'].mean() * 1e4:+.0f} bps/call"]
    lines += ["", "**Top trades going into the week:** "
              + ", ".join(f"{t['side']} {t['ticker']}"
                          for t in result.get("trades", []))]
    lines += ["", "**Coach's standing read:** see Past Trades → the coach; "
              "log every trade in the journal — the sample is the product.", ""]
    out_dir = config.REPORTS_DIR / "digests"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"digest_{date.today().isoformat()}.md"
    path.write_text("\n".join(lines))
    notify("Vig — weekly digest", "Week reviewed — digest in reports/digests/")
    return str(path)


def backup_state(root=None) -> None:
    """Version the small run artifacts in git — the ledger IS the track
    record; losing it would be losing the desk's memory."""
    root = str(root or config.ROOT)
    try:
        subprocess.run(["git", "-C", root, "add",
                        "reports/ledger", "reports/briefs", "reports/digests",
                        "reports/state.json", "reports/data_verification.csv"],
                       check=False, capture_output=True, timeout=30)
        subprocess.run(["git", "-C", root, "commit", "-q",
                        "-m", f"vig: daily state {date.today().isoformat()}"],
                       check=False, capture_output=True, timeout=30)
    except Exception:  # noqa: BLE001
        pass
