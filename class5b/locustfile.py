"""Concurrent CrewAI crews against the gateway.

Each Locust user runs one crew at a time (researcher, then writer), the same
path as `python app.py`. Users run at the same time, so `-u 4` is four crews
in flight. The technique label comes from LOCUST_TECHNIQUE or VLLM_SERVER_PROFILE.

  locust -f locustfile.py
  locust -f locustfile.py --headless -u 4 -r 1 -t 60s
"""

from __future__ import annotations

import os
import time

from locust import User, constant, events, task

from app import (
    _exit_if_gateway_shows_bad_vllm_url,
    _setup_otel,
    _wait_for_vllm_via_gateway,
    build_crew,
)

TECHNIQUE = (
    os.environ.get("LOCUST_TECHNIQUE")
    or os.environ.get("VLLM_SERVER_PROFILE")
    or "tensor_parallel"
)


@events.test_start.add_listener
def _on_test_start(environment, **kwargs):
    _ = (environment, kwargs)
    _exit_if_gateway_shows_bad_vllm_url()
    _wait_for_vllm_via_gateway()
    _setup_otel()


class CrewUser(User):
    """One user, one crew. Locust starts `users` of these together."""

    # The crew itself is the wait. Do not add another pause between kicks.
    wait_time = constant(0)

    @task
    def kickoff(self) -> None:
        start = time.perf_counter()
        exception: Exception | None = None
        length = 0
        try:
            result = build_crew(TECHNIQUE, verbose=False).kickoff()
            length = len(str(result))
        except Exception as exc:
            exception = exc
        elapsed_ms = (time.perf_counter() - start) * 1000
        events.request.fire(
            request_type="CREW",
            name=f"kickoff {TECHNIQUE}",
            response_time=elapsed_ms,
            response_length=length,
            exception=exception,
            context={},
        )
