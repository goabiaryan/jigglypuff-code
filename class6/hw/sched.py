from __future__ import annotations

from schema import Request, StepStats


def step(
    waiting: list[Request],
    running: list[Request],
    budget: int,
    *,
    policy: str = "fcfs",
    kv_free: int = 10_000,
    stats: StepStats | None = None,
) -> tuple[list[Request], list[Request], StepStats]:
    raise NotImplementedError("hw/README.md Part 2")
