"""A circuit breaker plus a fallback model: fail fast, then route around the failure.

When the primary model starts timing out, every request that still waits for
it pays the full timeout before failing. A breaker counts failures, opens
after a threshold and sends traffic straight to the fallback; after a cool-down
it lets one probe through to see if the primary is healthy again.

Run:  uv run python lessons/19-reliability-cost-llmops/code/03_circuit_breaker_fallback.py
      INJECT_NO_BREAKER=1 uv run python lessons/19-reliability-cost-llmops/code/03_circuit_breaker_fallback.py
Expect: with the breaker, only a few probes wait on the sick primary, the rest go
        straight to the fallback, and the circuit closes again once the primary recovers.
        Without it, every call during the outage waits out the full timeout.
"""

# %% imports
import asyncio
import os
import time
from enum import StrEnum

from aiapp import FakeAdapter, Message, ModelAdapter, ModelResponse, ToolSpec

INJECT_NO_BREAKER = os.environ.get("INJECT_NO_BREAKER") == "1"
PRIMARY_TIMEOUT = 0.05


# %% sick_primary
class SickPrimary(FakeAdapter):
    """Hangs on every call for the first `sick_for` seconds, then recovers."""

    name = "primary"

    def __init__(self, sick_for: float) -> None:
        super().__init__()
        self.recover_at = time.monotonic() + sick_for
        self.attempts = 0

    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse:
        self.attempts += 1
        if time.monotonic() < self.recover_at:
            await asyncio.sleep(PRIMARY_TIMEOUT * 2)  # will be cut off by the caller's timeout
        return ModelResponse(content="primary answer")


# %% circuit_breaker
class State(StrEnum):
    CLOSED = "closed"  # normal
    OPEN = "open"  # failing; skip primary
    HALF_OPEN = "half_open"  # cool-down over; allow one probe


class CircuitBreaker:
    def __init__(self, *, failure_threshold: int, recovery_timeout: float) -> None:
        self.failure_threshold, self.recovery_timeout = failure_threshold, recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.opened_at = 0.0

    def allow(self) -> bool:
        if self.state == State.OPEN and time.monotonic() - self.opened_at >= self.recovery_timeout:
            self.state = State.HALF_OPEN
        return self.state != State.OPEN

    def record_success(self) -> None:
        self.state, self.failures = State.CLOSED, 0

    def record_failure(self) -> None:
        self.failures += 1
        if self.state == State.HALF_OPEN or self.failures >= self.failure_threshold:
            self.state, self.opened_at = State.OPEN, time.monotonic()


# %% router
class ModelRouter:
    def __init__(self, primary: ModelAdapter, fallback: ModelAdapter, breaker: CircuitBreaker | None) -> None:
        self.primary, self.fallback, self.breaker = primary, fallback, breaker
        self.served_by: dict[str, int] = {"primary": 0, "fallback": 0}

    async def complete(self, messages: list[Message]) -> ModelResponse:
        if self.breaker is None or self.breaker.allow():
            try:
                reply = await asyncio.wait_for(self.primary.complete(messages), PRIMARY_TIMEOUT)
                if self.breaker:
                    self.breaker.record_success()
                self.served_by["primary"] += 1
                return reply
            except TimeoutError:
                if self.breaker:
                    self.breaker.record_failure()
        self.served_by["fallback"] += 1
        return await self.fallback.complete(messages)


# %% run
async def main() -> None:
    primary = SickPrimary(sick_for=0.6)
    fallback = FakeAdapter(script=[ModelResponse(content="fallback answer")] * 100)
    fallback.name = "fallback"
    breaker = None if INJECT_NO_BREAKER else CircuitBreaker(failure_threshold=3, recovery_timeout=0.15)
    router = ModelRouter(primary, fallback, breaker)

    start = time.monotonic()
    for i in range(30):
        reply = await router.complete([Message(role="user", content=f"q{i}")])
        state = breaker.state if breaker else "n/a"
        print(f"req {i:2}: {reply.content:16} breaker={state}")
        await asyncio.sleep(0.01)
    print(f"elapsed={time.monotonic() - start:.2f}s primary_attempts={primary.attempts} served_by={router.served_by}")


if __name__ == "__main__":
    asyncio.run(main())
