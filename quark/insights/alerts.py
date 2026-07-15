"""Event alerts, the Sunday digest, and daily state backup.

Alerts fire only on CHANGES (gate flips, new data flags) — the daily
top-trades notification already covers the routine. State is persisted in
reports/state.json between runs. Small run artifacts are committed to the
LOCAL git history (current branch, never pushed): that versions the ledger
against accidental edits, not against disk loss — offsite backup is the
MYVIG BACKUP button or your own push.
"""

import json
import math
import subprocess
from datetime import date

import pandas as pd

from quark import config

STATE_PATH = config.REPORTS_DIR / "state.json"


def _fmt_ic(v) -> str:
    return f"{v:+.3f}" if isinstance(v, (int, float)) and math.isfinite(v) \
        else "n/a"


def _snapshot(result: dict) -> dict:
    h = result.get("health", {})
    data_check = result.get("data_check", {})
    return {
        "date": str(date.today()),
        "model_status": h.get("model_status"),
        "ic_mean": h.get("ic_mean"),
        # None (not []) when cross-verification didn't run: "no information"
        # must not read as "no flags", or flags would re-alert as new after
        # every provider outage
        "data_flags": (sorted(data_check.get("flagged", []))
                       if data_check else None),
        "top": [f"{t['side']} {t['ticker']}" for t in result.get("trades", [])],
    }


def diff_events(prev: dict, cur: dict) -> list[str]:
    if not isinstance(prev, dict) or not prev:
        return []  # first run or corrupt state: no baseline, no alerts
    events = []
    ps, cs = prev.get("model_status"), cur.get("model_status")
    if ps and cs and ps != cs:
        sev = "✓" if cs == "green" else "⚠️"
        events.append(f"{sev} trust gate {ps} → {cs} "
                      f"(26w IC {_fmt_ic(cur.get('ic_mean'))})")
    pf, cf = prev.get("data_flags"), cur.get("data_flags")
    if pf is not None and cf is not None:
        new_flags = set(cf) - set(pf)
        if new_flags:
            events.append("⚠️ data cross-check flagged: "
                          + ", ".join(sorted(new_flags)))
    return events


def notify(title: str, msg: str) -> None:
    try:
        # escape for the AppleScript string literal: a stray quote in a
        # ticker or detail string must not kill (or script) the notification
        t = title.replace("\\", "\\\\").replace('"', '\\"')
        m = msg.replace("\\", "\\\\").replace('"', '\\"')
        subprocess.run(["osascript", "-e",
                        f'display notification "{m}" with title "{t}"'],
                       check=False, capture_output=True, timeout=10)
    except Exception:  # noqa: BLE001 — notifications are garnish
        pass


def run_alerts(result: dict) -> list[str]:
    prev = {}
    if STATE_PATH.exists():
        try:
            loaded = json.loads(STATE_PATH.read_text())
            prev = loaded if isinstance(loaded, dict) else {}
        except (json.JSONDecodeError, OSError):
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
    trades = review.get("trades") if isinstance(review, dict) else None
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


BACKUP_PATHS = ["reports/ledger", "reports/briefs", "reports/digests",
                "reports/state.json", "reports/data_verification.csv"]


def backup_state(root=None) -> None:
    """Locally version the small run artifacts — the ledger IS the track
    record; this protects it from accidental edits (offsite safety is the
    user's push / MYVIG BACKUP, stated in the module doc)."""
    from pathlib import Path
    rootp = Path(root or config.ROOT)
    try:
        # only paths that exist: `git add a b` (and `git commit -- a b`)
        # abort staging/committing EVERYTHING if any pathspec is missing,
        # and reports/digests doesn't exist until the first Sunday
        present = [p for p in BACKUP_PATHS if (rootp / p).exists()]
        for path in present:
            subprocess.run(["git", "-C", str(rootp), "add", path],
                           check=False, capture_output=True, timeout=30)
        # commit ONLY these paths — a bare `git commit` would sweep whatever
        # the user happens to have staged into the bot commit (audit-found)
        if present:
            subprocess.run(["git", "-C", str(rootp), "commit", "-q",
                            "-m", f"vig: daily state {date.today().isoformat()}",
                            "--"] + present,
                           check=False, capture_output=True, timeout=30)
    except Exception:  # noqa: BLE001
        pass
