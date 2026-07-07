"""Launched by Trader.app: open today's dashboard, regenerating it first if
stale. Kept dependency-light and fast on the happy path."""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DASH = ROOT / "reports" / "dashboard" / "index.html"
META = ROOT / "reports" / "dashboard" / "meta.json"


def notify(text: str) -> None:
    subprocess.run(
        ["osascript", "-e",
         f'display notification "{text}" with title "Quark Trader"'],
        check=False,
    )


def is_fresh() -> bool:
    if not (DASH.exists() and META.exists()):
        return False
    try:
        meta = json.loads(META.read_text())
        return meta["generated_at"][:10] == date.today().isoformat()
    except (json.JSONDecodeError, KeyError):
        return False


def main() -> None:
    if not is_fresh():
        notify("Updating market data and retraining — dashboard opens when ready (~3 min)")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "update_dashboard.py")],
            cwd=ROOT, check=False,
        )
        if proc.returncode != 0 and DASH.exists():
            notify("Update failed — showing the last good dashboard")
        elif proc.returncode == 0:
            notify("Dashboard updated")
    if DASH.exists():
        subprocess.run(["open", str(DASH)], check=False)
    else:
        notify("No dashboard yet and the update failed — run update_dashboard.py manually")


if __name__ == "__main__":
    main()
