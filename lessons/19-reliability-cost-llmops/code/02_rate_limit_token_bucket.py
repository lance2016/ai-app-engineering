"""Client-side rate limiting: spend the provider's quota on purpose, not by accident.

Every provider enforces a concurrency or requests-per-minute limit and answers
429 when you exceed it. Discovering that limit by getting rejected is the
expensive way. A token bucket in front of the client smooths bursts so the
downstream never sees more than it allows.

Run:  uv run python lessons/19-reliability-cost-llmops/code/02_rate_limit_token_bucket.py
      INJECT_NO_LIMIT=1 uv run python lessons/19-reliability-cost-llmops/code/02_rate_limit_token_bucket.py
Expect: with the bucket, all 12 requests succeed, evenly spaced.
        Without it, the burst hits the downstream limit and 7 of 12 get 429.
"""

# %% imports
import asyncio
import os
import time

INJECT_NO_LIMIT = os.environ.get("INJECT_NO_LIMIT") == "1"
SCALE = 0.02  # one "second" of the demo is 20 ms


# %% token_bucket
class TokenBucket:
    """`rate` tokens are added per (scaled) second, up to `capacity`. acquire() waits for one."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate, self.capacity = rate, capacity
        self.tokens = float(capacity)
        self.updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.updated) / SCALE * self.rate)
                self.updated = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                await asyncio.sleep((1 - self.tokens) / self.rate * SCALE)


# %% strict_downstream
class Downstream:
    """Allows at most `limit` requests per sliding (scaled) second, like a provider's RPM limit."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.stamps: list[float] = []
        self.ok = self.rejected = 0

    async def call(self, i: int) -> None:
        now = time.monotonic()
        self.stamps = [s for s in self.stamps if now - s < SCALE]
        if len(self.stamps) >= self.limit:
            self.rejected += 1
            print(f"req {i:2}: 429 Too Many Requests")
            return
        self.stamps.append(now)
        self.ok += 1
        print(f"req {i:2}: 200 at t={now - START:.3f}s")


START = time.monotonic()


# %% run
async def main() -> None:
    downstream = Downstream(limit=5)
    bucket = TokenBucket(rate=5, capacity=1)  # capacity 1: smooth, never bursts past a sliding-window limit

    async def one(i: int) -> None:
        if not INJECT_NO_LIMIT:
            await bucket.acquire()
        await downstream.call(i)

    await asyncio.gather(*(one(i) for i in range(12)))
    print(f"ok={downstream.ok} rejected={downstream.rejected} elapsed={time.monotonic() - START:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())
