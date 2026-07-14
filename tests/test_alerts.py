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
    assert diff_events({}, state) == []          # first run: no prior, no alert
    # flags clearing is good news, not an alert
    assert diff_events({"model_status": "green", "data_flags": ["X"]},
                       {"model_status": "green", "data_flags": []}) == []
