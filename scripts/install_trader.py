"""Install the Trader experience on this Mac:

1. Trader.app (Spotlight-launchable) that opens/refreshes the dashboard.
2. A launchd agent that refreshes data + regenerates the dashboard every
   morning at 07:15 (missed runs fire on wake).

Idempotent — re-run any time. Uninstall notes are printed at the end.
"""

import plistlib
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
LABEL = "com.quark.trader.daily"
AGENT = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = ROOT / "reports" / "logs"


def build_app() -> Path:
    script = (
        f'do shell script "{PYTHON} '
        f'{ROOT / "scripts" / "trader_open.py"} '
        f'>> {LOG_DIR / "trader_app.log"} 2>&1"'
    )
    candidates = [Path("/Applications"), Path.home() / "Applications"]
    for base in candidates:
        try:
            base.mkdir(exist_ok=True)
            app = base / "Trader.app"
            with tempfile.NamedTemporaryFile("w", suffix=".applescript",
                                             delete=False) as f:
                f.write(script)
                src = f.name
            subprocess.run(["osacompile", "-o", str(app), src], check=True)
            return app
        except (PermissionError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("could not write Trader.app to /Applications or ~/Applications")


def install_agent() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    plist = {
        "Label": LABEL,
        "ProgramArguments": [PYTHON, str(ROOT / "scripts" / "update_dashboard.py")],
        "WorkingDirectory": str(ROOT),
        "StartCalendarInterval": {"Hour": 7, "Minute": 15},
        "StandardOutPath": str(LOG_DIR / "daily.log"),
        "StandardErrorPath": str(LOG_DIR / "daily.log"),
    }
    AGENT.parent.mkdir(parents=True, exist_ok=True)
    with open(AGENT, "wb") as f:
        plistlib.dump(plist, f)
    subprocess.run(["launchctl", "unload", str(AGENT)], check=False,
                   capture_output=True)
    subprocess.run(["launchctl", "load", "-w", str(AGENT)], check=True)


def main() -> None:
    app = build_app()
    print(f"Installed {app} — launch with Cmd+Space, type 'Trader'")
    install_agent()
    print(f"Scheduled daily refresh 07:15 via {AGENT}")
    print("\nUninstall:")
    print(f"  launchctl unload -w {AGENT} && rm {AGENT}")
    print(f"  rm -rf {app}")


if __name__ == "__main__":
    main()
