"""Timeouts with retries, the circuit breaker, and the fallback adapter (lesson 19 in aiapp.ops)."""

import asyncio

import pytest

from aiapp import FakeAdapter, Message, ModelResponse
from aiapp.adapters.inject import FailingAdapter, SlowAdapter
from aiapp.ops.resilience import BreakerState, CircuitBreaker, FallbackAdapter, RetryableError, with_timeout_retry

pytestmark = pytest.mark.anyio


async def test_retry_only_what_can_succeed() -> None:
    calls = {"n": 0}

    async def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise RetryableError("429")
        return "ok"

    assert await with_timeout_retry(flaky, attempts=4, base_s=0.001, cap_s=0.002) == "ok" and calls["n"] == 3

    async def bad_request() -> str:
        raise ValueError("400 bad request")

    with pytest.raises(ValueError):
        await with_timeout_retry(bad_request, attempts=4, base_s=0.001, cap_s=0.002)

    async def hangs() -> str:
        await asyncio.sleep(1)
        return "late"

    with pytest.raises(RuntimeError, match="gave up after 2"):
        await with_timeout_retry(hangs, attempts=2, per_attempt_timeout_s=0.01, base_s=0.001, cap_s=0.002)


def test_breaker_opens_after_threshold_and_half_opens_after_cooldown() -> None:
    b = CircuitBreaker(failure_threshold=2, recovery_timeout_s=0.05)
    assert b.allow() and b.state == BreakerState.CLOSED
    b.record_failure()
    assert b.allow()
    b.record_failure()
    assert b.state == BreakerState.OPEN and not b.allow()
    import time

    time.sleep(0.06)
    assert b.allow() and b.state == BreakerState.HALF_OPEN
    b.record_failure()
    assert b.state == BreakerState.OPEN, "a failed probe re-opens immediately"
    time.sleep(0.06)
    assert b.allow()
    b.record_success()
    assert b.state == BreakerState.CLOSED and b.failures == 0


async def test_fallback_serves_when_primary_fails_and_skips_it_once_open() -> None:
    primary = FailingAdapter(FakeAdapter(), "down")
    secondary = FakeAdapter(script=[ModelResponse(content="fallback")] * 10)
    secondary.name = "secondary"
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout_s=60)
    adapter = FallbackAdapter(primary, secondary, breaker, primary_timeout_s=0.2)
    for _ in range(4):
        reply = await adapter.complete([Message(role="user", content="hi")])
        assert reply.content == "fallback"
    assert breaker.state == BreakerState.OPEN and adapter.served_by == {"primary": 0, "fallback": 4}
    assert adapter.name == "failing(fake)|secondary"


async def test_fallback_stream_switches_only_before_first_chunk() -> None:
    slow = SlowAdapter(FakeAdapter(script=[ModelResponse(content="primary")]), delay_s=5)
    secondary = FakeAdapter(script=[ModelResponse(content="from fallback")], chunk_size=100)
    adapter = FallbackAdapter(slow, secondary, CircuitBreaker(), primary_timeout_s=0.05)
    chunks = [c async for c in adapter.stream([Message(role="user", content="hi")])]
    assert "".join(c.delta for c in chunks) == "from fallback" and adapter.last_served_by == "fallback"

    healthy = FakeAdapter(script=[ModelResponse(content="primary text")], chunk_size=100)
    adapter = FallbackAdapter(healthy, secondary, CircuitBreaker(), primary_timeout_s=1)
    chunks = [c async for c in adapter.stream([Message(role="user", content="hi")])]
    assert "".join(c.delta for c in chunks) == "primary text" and adapter.last_served_by == "primary"
