from __future__ import annotations

from admit import should_shed
from router import pick
from sched import step
from schema import Request, Shed, StepStats, Worker


def handle(req: Request, workers: list[Worker], *, policy: str = "p2c") -> Worker | Shed:
    raise NotImplementedError("hw/README.md Part 4")


def run_step(workers: list[Worker], budget: int, *, sched_policy: str = "priority") -> StepStats:
    raise NotImplementedError("hw/README.md Part 4")
