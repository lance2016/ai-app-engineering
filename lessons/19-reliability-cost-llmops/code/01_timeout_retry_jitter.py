"""Timeouts and retries: only retry what can succeed on a second try, and never in lockstep.

A model call can hang, get a 429, or fail with a 500. Those are worth retrying,
with a deadline on each attempt and a randomised (jittered) back-off so that
a thousand clients do not retry at the same instant. A 400 or an auth error
is not worth retrying at all; retrying it just burns time and hides the bug.

Run:  uv run python lessons/19-reliability-cost-llmops/code/01_timeout_retry_jitter.py
      INJECT_ALWAYS_FAIL=1 uv run python lessons/19-reliability-cost-llmops/code/01_timeout_retry_jitter.py
      INJECT_BAD_REQUEST=1 uv run python lessons/19-reliability-cost-llmops/code/01_timeout_retry_jitter.py
Expect: normally success on attempt 2 or 3; with ALWAYS_FAIL a clean give-up
        after the cap; with BAD_REQUEST no retry at all.
"""

# %% imports
import asyncio
import os
import random
from collections.abc import Awaitable, Callable

INJECT_ALWAYS_FAIL = os.environ.get("INJECT_ALWAYS_FAIL") == "1"
INJECT_BAD_REQUEST = os.environ.get("INJECT_BAD_REQUEST") == "1"
SLEEP_SCALE = 0.01  # keep the demo fast; production uses seconds, not hundredths


# %% error_taxonomy
class RateLimited(Exception):
    """HTTP 429. Retryable, ideally honouring Retry-After."""


class UpstreamError(Exception):
    """HTTP 5xx. Retryable."""


class BadRequest(Exception):
    """HTTP 4xx other than 429. Not retryable: the request itself is wrong."""


RETRYABLE = (TimeoutError, RateLimited, UpstreamError)


# %% flaky_downstream
class FlakyModel:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, prompt: str) -> str:
        self.calls += 1
        if INJECT_BAD_REQUEST:
            raise BadRequest("messages[0].role must be one of system,user,assistant")
        if INJECT_ALWAYS_FAIL or self.calls == 1:
            await asyncio.sleep(5 * SLEEP_SCALE)  # hangs past the per-attempt deadline
            return "too late"
        if self.calls == 2:
            raise RateLimited("429 slow down")
        return f"answer to {prompt!r}"


# %% retry_with_full_jitter
def backoff(attempt: int, *, base: float, cap: float) -> float:
    """'Full jitter': uniform between 0 and min(cap, base * 2**attempt)."""
    return random.uniform(0, min(cap, base * (2**attempt)))


async def call_with_retry(
    fn: Callable[[], Awaitable[str]], *, attempts: int, per_attempt_timeout: float, base: float, cap: float
) -> str:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            return await asyncio.wait_for(fn(), timeout=per_attempt_timeout)
        except RETRYABLE as exc:
            last = exc
            if attempt == attempts - 1:
                break
            delay = backoff(attempt, base=base, cap=cap)
            print(f"attempt {attempt + 1}: {type(exc).__name__} -> retry in {delay:.3f}s")
            await asyncio.sleep(delay)
        except BadRequest as exc:
            print(f"attempt {attempt + 1}: {type(exc).__name__} -> not retryable, giving up now")
            raise
    raise RuntimeError(f"gave up after {attempts} attempts: {last!r}")


# %% run
async def main() -> None:
    model = FlakyModel()
    try:
        answer = await call_with_retry(
            lambda: model.complete("hello"),
            attempts=4,
            per_attempt_timeout=2 * SLEEP_SCALE,
            base=1 * SLEEP_SCALE,
            cap=8 * SLEEP_SCALE,
        )
        print(f"ok after {model.calls} call(s): {answer}")
    except (RuntimeError, BadRequest) as exc:
        print(f"failed after {model.calls} call(s): {exc}")


if __name__ == "__main__":
    asyncio.run(main())
