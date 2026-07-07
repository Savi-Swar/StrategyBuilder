"""Purged, embargoed walk-forward splits.

Expanding train window, one test fold per calendar year. Between train end
and test start we drop `purge + embargo` bars: `purge` >= the target horizon
guarantees no training target overlaps a test date; `embargo` adds slack for
serial correlation. tests/test_splits.py asserts the gap on every fold.
"""

from collections.abc import Iterator

import pandas as pd

from quark import config


class PurgedWalkForward:
    def __init__(
        self,
        dates: pd.DatetimeIndex,
        first_test_year: int = config.FIRST_TEST_YEAR,
        purge: int = config.PURGE_DAYS,
        embargo: int = config.EMBARGO_DAYS,
    ):
        self.dates = pd.DatetimeIndex(dates).sort_values().unique()
        self.first_test_year = first_test_year
        self.purge = purge
        self.embargo = embargo

    def split(self) -> Iterator[tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
        last_year = self.dates[-1].year
        for year in range(self.first_test_year, last_year + 1):
            test_start = self.dates.searchsorted(pd.Timestamp(year, 1, 1))
            test_end = self.dates.searchsorted(pd.Timestamp(year + 1, 1, 1))
            if test_start >= len(self.dates) or test_start == test_end:
                continue
            train_end = test_start - self.purge - self.embargo
            if train_end <= 0:
                continue
            yield self.dates[:train_end], self.dates[test_start:test_end]
