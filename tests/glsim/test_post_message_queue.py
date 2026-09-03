from glsim.engine import SimEngine
from glsim.state import StateStore


def test_drain_post_queue_executes_all_messages_in_order(monkeypatch):
    engine = SimEngine(StateStore())
    engine._post_queue = [
        {
            "address": "0x01",
            "method": "first",
            "args": [1],
            "kwargs": {},
            "sender": "0xaa",
        },
        {
            "address": "0x02",
            "method": "second",
            "args": [2],
            "kwargs": {},
            "sender": "0xbb",
        },
    ]
    calls = []

    def fake_call(address, method, args, kwargs, sender):
        calls.append((address, method, args, sender))
        if method == "first":
            engine._post_queue.append(
                {
                    "address": "0x03",
                    "method": "nested",
                    "args": [3],
                    "kwargs": {},
                    "sender": "0xcc",
                }
            )

    monkeypatch.setattr(engine, "call_method", fake_call)

    engine._drain_post_queue()

    assert [call[1] for call in calls] == ["first", "second", "nested"]
    assert engine._post_queue == []
    assert engine._draining is False
