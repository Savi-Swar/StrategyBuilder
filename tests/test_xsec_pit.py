import pandas as pd

from quark.ml.xsec import apply_membership, hysteresis_weights


def test_weekend_snapshot_still_governs_following_days():
    """Audit-pinned: ~2/7 of calendar month-ends are non-trading days; a
    straight reindex to trading days would DROP those snapshots and leave
    membership stale by an extra month."""
    days = pd.bdate_range("2005-04-25", "2005-05-13")
    elig = pd.DataFrame(True, index=days, columns=["A", "B"])
    # 2005-04-30 is a Saturday — A leaves the index in that snapshot
    membership = pd.DataFrame(
        [[True, True], [False, True]],
        index=pd.to_datetime(["2005-03-31", "2005-04-30"]),
        columns=["A", "B"])
    out = apply_membership(elig, membership)
    assert out.loc["2005-04-29", "A"]        # Friday: last day as a member
    assert not out.loc["2005-05-02", "A"]    # Monday after the Sat snapshot
    assert out["B"].all()


def test_no_membership_before_first_snapshot():
    days = pd.bdate_range("2005-01-03", "2005-04-08")
    elig = pd.DataFrame(True, index=days, columns=["A"])
    membership = pd.DataFrame(
        [[True]], index=pd.to_datetime(["2005-03-31"]), columns=["A"])
    out = apply_membership(elig, membership)
    assert not out.loc["2005-03-30", "A"]    # unknown -> not eligible
    assert out.loc["2005-03-31", "A"]


def test_hysteresis_holds_within_band_and_exits_past_it():
    # 20 names; probs are permutations so rank pcts are exact multiples of .05
    tickers = [f"T{i:02d}" for i in range(20)]
    dates = pd.to_datetime(["2020-01-03", "2020-01-10", "2020-01-17"])
    base = list(range(20))                    # T00 lowest ... T19 highest
    day2 = base.copy()
    day2[19], day2[14] = base[14], base[19]   # T19 decays to pct 0.75
    day3 = base.copy()
    day3[19], day3[11] = base[11], base[19]   # T19 decays to pct 0.60
    preds = pd.DataFrame([base, day2, day3], index=dates, columns=tickers,
                         dtype=float)

    w30 = hysteresis_weights(preds, exit_gap=0.30)
    assert w30.loc[dates[0], "T19"] > 0       # entered: pct 1.0 > 0.90
    assert w30.loc[dates[1], "T19"] > 0       # pct 0.75 > 0.60 -> held
    assert w30.loc[dates[2], "T19"] == 0      # pct 0.60 -> exit

    w15 = hysteresis_weights(preds, exit_gap=0.15)
    assert w15.loc[dates[1], "T19"] == 0      # pct 0.75 not > 0.75 -> exit

    # equal-weight sides at +/-50% gross whenever both sides are populated
    row = w30.loc[dates[1]]
    assert abs(row[row > 0].sum() - 0.5) < 1e-12
    assert abs(row[row < 0].sum() + 0.5) < 1e-12

    # with no decay the book never trades after entry: zero turnover
    flat = pd.DataFrame([base, base, base], index=dates, columns=tickers,
                        dtype=float)
    wflat = hysteresis_weights(flat, exit_gap=0.15)
    assert (wflat.diff().dropna() == 0).all().all()


def test_backup_paths_added_individually(tmp_path):
    """Audit-pinned: `git add a b` stages NOTHING (exit 128) if any pathspec
    is missing — and reports/digests doesn't exist until the first Sunday."""
    import subprocess

    from quark.insights import alerts
    root = tmp_path
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "t@t"],
                   check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "t"],
                   check=True)
    (root / "reports").mkdir()
    (root / "reports" / "state.json").write_text("{}")
    # reports/digests, ledger, briefs deliberately absent
    # audit-pinned: user-staged files must NOT be swept into the bot commit
    (root / "secret.txt").write_text("user work in progress")
    subprocess.run(["git", "-C", str(root), "add", "secret.txt"], check=True)

    alerts.backup_state(root=root)
    log = subprocess.run(["git", "-C", str(root), "log", "--oneline"],
                         capture_output=True, text=True)
    assert "vig: daily state" in log.stdout   # commit landed despite gaps
    shown = subprocess.run(["git", "-C", str(root), "show", "--stat",
                            "--name-only", "HEAD"],
                           capture_output=True, text=True).stdout
    assert "state.json" in shown and "secret.txt" not in shown
    staged = subprocess.run(["git", "-C", str(root), "diff", "--cached",
                             "--name-only"], capture_output=True, text=True)
    assert "secret.txt" in staged.stdout      # still staged, untouched
