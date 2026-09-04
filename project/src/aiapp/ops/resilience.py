"""Timeouts with jittered retries, a circuit breaker, and a fallback adapter that routes around a sick primary (lesson 19)."""

import asyncio
import logging
import random
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar

from aiapp.adapters.base import Message, ModelAdapter, ModelResponse, StreamChunk, ToolSpec

log = logging.getLogger("aiapp.ops")
T = TypeVar("T")


class RetryableError(Exception):
    """Raise this (or a TimeoutError) from a call to ask for a retry. Anything else is returned to the caller as is."""


def backoff(attempt: int, *, base: float, cap: float) -> float:
    """Full jitter: uniform between 0 and min(cap, base * 2**attempt)."""
    return random.uniform(0, min(cap, base * (2**attempt)))


async def with_timeout_retry(fn: Callable[[], Awaitable[T]], *, attempts: int = 3, per_attempt_timeout_s: float = 30.0, base_s: float = 0.2, cap_s: float = 5.0) -> T:
    last: BaseException | None = None
    for attempt in range(attempts):
        try:
            async with asyncio.timeout(per_attempt_timeout_s):
                return await fn()
        except (TimeoutError, RetryableError) as exc:
            last = exc
            if attempt == attempts - 1:
                break
            delay = backoff(attempt, base=base_s, cap=cap_s)
            log.warning("retryable failure attempt=%s type=%s retry_in=%.3fs", attempt + 1, type(exc).__name__, delay)
            await asyncio.sleep(delay)
    raise RuntimeError(f"gave up after {attempts} attempts: {last!r}") from last


class BreakerState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_s: float = 30.0
    state: BreakerState = BreakerState.CLOSED
    failures: int = 0
    opened_at: float = 0.0
    transitions: list[tuple[float, BreakerState]] = field(default_factory=list)

    def allow(self) -> bool:
        if self.state == BreakerState.OPEN and time.monotonic() - self.opened_at >= self.recovery_timeout_s:
            self._set(BreakerState.HALF_OPEN)
        return self.state != BreakerState.OPEN

    def record_success(self) -> None:
        self.failures = 0
        if self.state != BreakerState.CLOSED:
            self._set(BreakerState.CLOSED)

    def record_failure(self) -> None:
        self.failures += 1
        if self.state == BreakerState.HALF_OPEN or self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic()
            self._set(BreakerState.OPEN)

    def _set(self, state: BreakerState) -> None:
        self.state = state
        self.transitions.append((time.monotonic(), state))
        log.warning("circuit breaker -> %s (failures=%s)", state, self.failures)


class FallbackAdapter:
    """Try the primary under a timeout and a breaker; on an open circuit or a failure, use the secondary and say so.

    Streams switch to the secondary only if the primary fails *before its first chunk*: once text has started
    flowing there is no clean way to restart without the client seeing a duplicated answer.
    """

    def __init__(self, primary: ModelAdapter, secondary: ModelAdapter, breaker: CircuitBreaker | None = None, *, primary_timeout_s: float = 30.0):
        self.primary, self.secondary = primary, secondary
        self.breaker = breaker or CircuitBreaker()
        self.primary_timeout_s = primary_timeout_s
        self.name = f"{primary.name}|{secondary.name}"
        self.served_by: dict[str, int] = {"primary": 0, "fallback": 0}
        self.last_served_by: str = "primary"

    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse:
        if self.breaker.allow():
            try:
                async with asyncio.timeout(self.primary_timeout_s):
                    reply = await self.primary.complete(messages, tools)
                self.breaker.record_success()
                return self._served("primary", reply)
            except Exception as exc:
                self.breaker.record_failure()
                log.warning("primary %s failed (%s); falling back to %s", self.primary.name, type(exc).__name__, self.secondary.name)
        return self._served("fallback", await self.secondary.complete(messages, tools))

    async def stream(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> AsyncIterator[StreamChunk]:
        if self.breaker.allow():
            primary_stream = self.primary.stream(messages, tools)
            try:
                async with asyncio.timeout(self.primary_timeout_s):
                    first = await anext(primary_stream)
            except Exception as exc:
                self.breaker.record_failure()
                log.warning("primary %s failed before first chunk (%s); streaming from %s", self.primary.name, type(exc).__name__, self.secondary.name)
                await primary_stream.aclose()
            else:
                self.breaker.record_success()
                self._served("primary", None)
                yield first
                async for chunk in primary_stream:
                    yield chunk
                return
        self._served("fallback", None)
        async for chunk in self.secondary.stream(messages, tools):
            yield chunk

    def _served(self, who: str, reply: ModelResponse | None) -> ModelResponse | None:
        self.served_by[who] += 1
        self.last_served_by = who
        return reply
