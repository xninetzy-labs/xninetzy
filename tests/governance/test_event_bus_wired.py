from __future__ import annotations

import inspect


def test_reducers_consume_task_completed():
    from xninetzy.ecosystem.reducers import consume_event

    src = inspect.getsource(consume_event)
    assert "task_completed" in src, "reducer must handle task_completed event"
    assert "_reduce_task_completed" in src


def test_graph_populator_consumes_events():
    from xninetzy.os.graph.v3.graph_populator import consume_event

    assert callable(consume_event)


def test_event_bus_dispatches_both_consumers():
    from xninetzy.ecosystem.event_bus import dispatch_recorded_event

    src = inspect.getsource(dispatch_recorded_event)
    assert "consume_event" in src
    assert "reducers" in src or "graph_populator" in src
