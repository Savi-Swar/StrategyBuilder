from quark.insights.alerts import diff_events


def test_gate_flip_and_new_flags_fire():
    prev = {"model_status": "green", "data_flags": ["AAPL"]}
    cur = {"model_status": "yellow", "ic_mean": 0.002,
           "data_flags": ["AAPL", "NUE"]}
    events = diff_events(prev, cur)
    assert len(events) == 2
    assert "green → yellow" in events[0]
    assert "NUE" in events[1] and "AAPL" not in events[1]  # only NEW flags


def test_steady_state_is_silent():
    state = {"model_status": "green", "ic_mean": 0.01, "data_flags": []}
    assert diff_events(state, state) == []
    # flags clearing is good news, not an alert
    assert diff_events({"model_status": "green", "data_flags": ["X"]},
                       {"model_status": "green", "data_flags": []}) == []


def test_first_run_and_unknown_states_stay_silent():
    """Audit-pinned: no baseline -> no alerts (even with pre-existing flags),
    and a run where cross-verify didn't happen (data_flags=None) must not
    make old flags re-alert as 'new' afterwards."""
    cur = {"model_status": "green", "ic_mean": 0.01, "data_flags": ["AAPL"]}
    assert diff_events({}, cur) == []            # first run
    assert diff_events(None, cur) == []          # corrupt state file
    outage = {"model_status": "green", "data_flags": None}
    assert diff_events(outage, cur) == []        # unknown -> known: no alert
    assert diff_events(cur, outage) == []        # known -> unknown: no alert


def test_degrading_gate_is_flagged_and_nan_ic_renders():
    events = diff_events(
        {"model_status": "green", "data_flags": []},
        {"model_status": "warming", "ic_mean": float("nan"),
         "data_flags": []})
    assert len(events) == 1
    assert events[0].startswith("⚠️")            # leaving green is a warning
    assert "n/a" in events[0] and "nan" not in events[0]
