from __future__ import annotations

from schema import Request, Shed, Worker


def pick(
    req: Request,
    workers: list[Worker],
    *,
    policy: str = "p2c",
) -> Worker | Shed:
    raise NotImplementedError("hw/README.md Part 3")
