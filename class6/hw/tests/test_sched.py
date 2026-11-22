from __future__ import annotations

from sched import step
from schema import Request, StepStats


def _req(**kw) -> Request:
    base = dict(
        id="r0",
        arrival_t=0.0,
        priority=0,
        prompt_tokens=256,
        max_new_tokens=64,
        prefix_hash=None,
        timeout_s=30.0,
        tenant="lab",
    )
    base.update(kw)
    return Request(**base)


def test_abort_during_decode_frees_kv_and_emits_nothing() -> None:
    req = _req(id="abort-me", prefill_done=256, decode_done=8)
    req.aborted = True
    waiting: list[Request] = []
    running = [req]
    stats = StepStats()
    waiting, running, stats = step(waiting, running, budget=2048, stats=stats)
    assert req not in running
    assert stats.aborted_freed >= 1
    assert req.decode_done == 8
