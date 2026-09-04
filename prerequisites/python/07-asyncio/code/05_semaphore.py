"""Serial vs unlimited concurrency vs a Semaphore that caps it.

Run:  uv run python prerequisites/python/07-asyncio/code/05_semaphore.py
Expect: 8 jobs of 0.1s each: serial ~0.8s, unlimited ~0.1s, limit 3 ~0.3s.
"""

# %% imports
import asyncio
import time

N_JOBS = 8


# %% job
async def call_api(i: int, sem: asyncio.Semaphore | None = None) -> int:
    if sem is None:
        await asyncio.sleep(0.1)
        return i
    async with sem:  # at most `limit` jobs inside this block at once
        await asyncio.sleep(0.1)
        return i


# %% three_ways
async def serial() -> None:
    for i in range(N_JOBS):
        await call_api(i)


async def unlimited() -> None:
    await asyncio.gather(*(call_api(i) for i in range(N_JOBS)))


async def limited(limit: int) -> None:
    sem = asyncio.Semaphore(limit)
    await asyncio.gather(*(call_api(i, sem) for i in range(N_JOBS)))


# %% run
async def main() -> None:
    for label, coro in (("serial", serial()), ("unlimited", unlimited()), ("limit=3", limited(3))):
        t0 = time.perf_counter()
        await coro
        print(f"{label:10} {time.perf_counter() - t0:.2f}s")


asyncio.run(main())
