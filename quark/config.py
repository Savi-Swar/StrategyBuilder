"""Global configuration: paths, annualization, seeds, default parameters."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "Quark.db"
REPORTS_DIR = ROOT / "reports"

ANN_FACTOR = 252
SEED = 42

# Backtest defaults
VOL_TARGET = 0.10        # annualized per-instrument vol target
VOL_LOOKBACK = 63        # rolling window (days) for vol estimation
MAX_LEVERAGE = 4.0       # cap on vol-target scaling per instrument
EXECUTION_LAG = 1        # bars between signal and position

# ML defaults
TARGET_HORIZON = 5       # forward-return horizon (days)
FIRST_TEST_YEAR = 2012   # walk-forward out-of-sample starts here
PURGE_DAYS = 5           # >= TARGET_HORIZON so no train target overlaps test
EMBARGO_DAYS = 5
