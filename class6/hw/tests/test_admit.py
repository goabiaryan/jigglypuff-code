from __future__ import annotations

from admit import should_shed
from schema import Request, Snap

CAP = {503, 529}


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


def test_tenant_token_allowance_96_is_429() -> None:
    shed, code, _retry = should_shed(_req(), Snap(tenant_tokens_used=0.96))
    assert shed is True
    assert code == 429


def test_tenant_request_allowance_96_is_429() -> None:
    shed, code, _retry = should_shed(_req(), Snap(tenant_tokens_used=0.10, tenant_reqs_used=0.96))
    assert shed is True
    assert code == 429


def test_token_limit_is_checked_before_request_limit() -> None:
    shed, code, _retry = should_shed(_req(), Snap(tenant_tokens_used=0.96, tenant_reqs_used=0.96))
    assert shed is True
    assert code == 429


def test_queue_wait_over_half_timeout_is_503_or_529() -> None:
    snap = Snap(queue_len=10, p50_ttft_s=1.0)
    shed, code, _retry = should_shed(_req(timeout_s=10.0), snap)
    assert shed is True
    assert code in CAP


def test_low_kv_new_prefix_is_503_or_529() -> None:
    snap = Snap(kv_free=0.05, cached_prefixes=frozenset())
    shed, code, _retry = should_shed(_req(prefix_hash="new"), snap)
    assert shed is True
    assert code in CAP


def test_low_kv_cached_prefix_is_accepted() -> None:
    snap = Snap(kv_free=0.05, cached_prefixes=frozenset({"share"}))
    shed, code, _retry = should_shed(_req(prefix_hash="share"), snap)
    assert shed is False


def test_bad_tail_interactive_is_accepted() -> None:
    snap = Snap(p50_ttft_s=0.1, p99_ttft_s=0.8, queue_growing=True)
    shed, _code, _retry = should_shed(_req(priority=0), snap)
    assert shed is False


def test_bad_tail_batch_is_rejected() -> None:
    snap = Snap(p50_ttft_s=0.1, p99_ttft_s=0.8, queue_growing=True)
    shed, code, _retry = should_shed(_req(priority=20), snap)
    assert shed is True
    assert code in CAP


def test_empty_fleet_tenant_over_tokens_stays_429() -> None:
    snap = Snap(tenant_tokens_used=0.96, kv_free=0.0, queue_len=0, unknown=True)
    shed, code, _retry = should_shed(_req(), snap)
    assert shed is True
    assert code == 429
