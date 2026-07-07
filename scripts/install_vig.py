"""Install Vig on this Mac (and clean up the old Trader install):

1. Vig.app (Spotlight-launchable) that opens/refreshes the daily desk.
2. A launchd agent regenerating everything at 07:15 daily (fires on wake
   if the laptop was asleep).

Idempotent — re-run any time (e.g. if the repo moves or python changes).
"""

import plistlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable
LABEL = "com.quark.vig.daily"
AGENT = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = ROOT / "reports" / "logs"

OLD_LABEL = "com.quark.trader.daily"
OLD_AGENT = Path.home() / "Library" / "LaunchAgents" / f"{OLD_LABEL}.plist"
OLD_APPS = [Path("/Applications/Trader.app"),
            Path.home() / "Applications" / "Trader.app"]


def remove_old_install() -> None:
    if OLD_AGENT.exists():
        subprocess.run(["launchctl", "unload", "-w", str(OLD_AGENT)],
                       check=False, capture_output=True)
        OLD_AGENT.unlink()
        print(f"Removed old agent {OLD_LABEL}")
    for app in OLD_APPS:
        if app.exists():
            shutil.rmtree(app)
            print(f"Removed {app}")


def build_app() -> Path:
    script = (
        f'do shell script "{PYTHON} '
        f'{ROOT / "scripts" / "vig_open.py"} '
        f'>> {LOG_DIR / "vig_app.log"} 2>&1"'
    )
    for base in (Path("/Applications"), Path.home() / "Applications"):
        try:
            base.mkdir(exist_ok=True)
            app = base / "Vig.app"
            with tempfile.NamedTemporaryFile("w", suffix=".applescript",
                                             delete=False) as f:
                f.write(script)
                src = f.name
            subprocess.run(["osacompile", "-o", str(app), src], check=True)
            return app
        except (PermissionError, subprocess.CalledProcessError):
            continue
    raise RuntimeError("could not write Vig.app to /Applications or ~/Applications")


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
    remove_old_install()
    app = build_app()
    print(f"Installed {app} — launch with Cmd+Space, type 'Vig'")
    install_agent()
    print(f"Scheduled daily refresh 07:15 via {AGENT}")
    print("\nUninstall:")
    print(f"  launchctl unload -w {AGENT} && rm {AGENT}")
    print(f"  rm -rf {app}")


if __name__ == "__main__":
    main()
