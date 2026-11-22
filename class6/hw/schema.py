from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Request:
    id: str
    arrival_t: float
    priority: int
    prompt_tokens: int
    max_new_tokens: int
    prefix_hash: str | None
    timeout_s: float
    tenant: str
    aborted: bool = False
    prefill_done: int = 0
    decode_done: int = 0


@dataclass
class Snap:
    tenant_tokens_used: float = 0.0
    tenant_reqs_used: float = 0.0
    queue_len: int = 0
    p50_ttft_s: float = 0.1
    p99_ttft_s: float = 0.1
    kv_free: float = 1.0
    cached_prefixes: frozenset[str] = field(default_factory=frozenset)
    queue_growing: bool = False
    healthy: bool = True
    unknown: bool = False
    running: int = 0
    waiting: int = 0
    age_s: float = 0.0


@dataclass
class Worker:
    id: str
    snap: Snap
    waiting: list[Request] = field(default_factory=list)
    running: list[Request] = field(default_factory=list)
    kv_used: int = 0
    kv_capacity: int = 50_000


@dataclass
class Shed:
    status: int
    retry_after: float = 2.0
    reason: str = ""


@dataclass
class StepStats:
    preempts: int = 0
    wasted_decode_tokens: int = 0
    aborted_freed: int = 0
