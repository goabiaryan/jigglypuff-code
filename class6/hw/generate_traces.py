from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRACES = ROOT / "traces"


def _write(name: str, rows: list[dict]) -> Path:
    TRACES.mkdir(parents=True, exist_ok=True)
    path = TRACES / name
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return path


def mixed(n: int = 400, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    t = 0.0
    for i in range(n):
        roll = rng.random()
        if roll < 0.70:
            row = dict(
                id=f"ix-{i}",
                arrival_t=round(t, 4),
                priority=0,
                prompt_tokens=rng.randint(200, 800),
                max_new_tokens=rng.randint(64, 256),
                prefix_hash=None,
                timeout_s=5.0,
                tenant="chat",
            )
        elif roll < 0.90:
            row = dict(
                id=f"batch-{i}",
                arrival_t=round(t, 4),
                priority=20,
                prompt_tokens=rng.randint(2_000, 8_000),
                max_new_tokens=rng.randint(512, 2_048),
                prefix_hash=None,
                timeout_s=30.0,
                tenant="batch",
            )
        else:
            row = dict(
                id=f"agent-{i}",
                arrival_t=round(t, 4),
                priority=0,
                prompt_tokens=4_000,
                max_new_tokens=128,
                prefix_hash="agent-share",
                timeout_s=8.0,
                tenant="agent",
            )
        rows.append(row)
        t += rng.uniform(0.05, 0.25)
    return rows


def t1_unique(n: int = 200, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    t = 0.0
    for i in range(n):
        rows.append(
            dict(
                id=f"u-{i}",
                arrival_t=round(t, 4),
                priority=0,
                prompt_tokens=rng.randint(200, 800),
                max_new_tokens=64,
                prefix_hash=f"uniq-{i}",
                timeout_s=8.0,
                tenant="lab",
            )
        )
        t += 0.1
    return rows


def t2_shared(n: int = 200, seed: int = 2) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    t = 0.0
    for i in range(n):
        shared = rng.random() < 0.40
        rows.append(
            dict(
                id=f"s-{i}",
                arrival_t=round(t, 4),
                priority=0,
                prompt_tokens=4_000 if shared else rng.randint(200, 800),
                max_new_tokens=64,
                prefix_hash="hot" if shared else f"cold-{i}",
                timeout_s=8.0,
                tenant="lab",
            )
        )
        t += 0.1
    return rows


def t3_stale(n: int = 200, seed: int = 3) -> list[dict]:
    return t1_unique(n, seed)


def main() -> None:
    _write("mixed.jsonl", mixed())
    _write("t1_unique.jsonl", t1_unique())
    _write("t2_shared.jsonl", t2_shared())
    _write("t3_stale.jsonl", t3_stale())
    print(f"wrote traces/ under {TRACES}")


if __name__ == "__main__":
    main()
