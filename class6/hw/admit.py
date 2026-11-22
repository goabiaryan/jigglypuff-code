from __future__ import annotations

from schema import Request, Snap


def should_shed(req: Request, snap: Snap) -> tuple[bool, int, float]:
    raise NotImplementedError("hw/README.md Part 1")
