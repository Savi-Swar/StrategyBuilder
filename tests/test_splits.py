import pandas as pd

from quark.ml.splits import PurgedWalkForward


def make_folds(purge=5, embargo=5):
    dates = pd.bdate_range("2008-01-01", "2015-12-31")
    wf = PurgedWalkForward(dates, first_test_year=2012, purge=purge, embargo=embargo)
    return dates, list(wf.split())


def test_purge_embargo_gap_on_every_fold():
    dates, folds = make_folds(purge=5, embargo=5)
    assert len(folds) == 4  # 2012..2015
    for train, test in folds:
        assert train.max() < test.min()
        # exactly purge+embargo dates dropped between train end and test start
        gap = dates.searchsorted(test.min()) - dates.searchsorted(train.max()) - 1
        assert gap == 10


def test_test_folds_tile_the_oos_period():
    dates, folds = make_folds()
    all_test = pd.DatetimeIndex([]).append([test for _, test in folds])
    expected = dates[dates.year >= 2012]
    assert (all_test == expected).all()


def test_expanding_train_window():
    dates, folds = make_folds()
    lengths = [len(train) for train, _ in folds]
    assert lengths == sorted(lengths)
    for train, _ in folds:
        assert train[0] == dates[0]


def test_no_test_date_in_any_train():
    _, folds = make_folds()
    for train, test in folds:
        assert len(train.intersection(test)) == 0
