from __future__ import annotations

from router import pick
from schema import Request, Shed, Snap, Worker


def _req(**kw) -> Request:
    base = dict(
        id="r0",
        arrival_t=0.0,
        priority=0,
        prompt_tokens=256,
        max_new_tokens=64,
        prefix_hash="p",
        timeout_s=10.0,
        tenant="lab",
    )
    base.update(kw)
    return Request(**base)


def test_both_workers_would_shed_returns_503() -> None:
    a = Worker("A", Snap(kv_free=0.02, tenant_tokens_used=0.0))
    b = Worker("B", Snap(kv_free=0.02, tenant_tokens_used=0.0))
    out = pick(_req(prefix_hash="new"), [a, b], policy="least_loaded")
    assert isinstance(out, Shed)
    assert out.status == 503
    assert out.retry_after == 2


def test_unknown_worker_is_not_treated_as_idle() -> None:
    busy = Worker("A", Snap(kv_free=0.9, running=1, waiting=0, unknown=False))
    stale = Worker("B", Snap(kv_free=1.0, running=0, waiting=0, unknown=True, age_s=15.0))
    picked = pick(_req(), [busy, stale], policy="least_loaded")
    assert not isinstance(picked, Shed)
    assert picked.id == "A"
