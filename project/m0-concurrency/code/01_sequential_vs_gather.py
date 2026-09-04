"""Five model calls, one after another vs all at once.

Run:  uv run python project/m0-concurrency/code/01_sequential_vs_gather.py
Expect: sequential takes ~5x the single-call latency; gather takes ~1x.
"""

# %% imports
import asyncio
import time

LATENCY = 0.2


# %% fake_call
async def call_model(i: int) -> str:
    await asyncio.sleep(LATENCY)  # network wait, not CPU work
    return f"reply {i}"


# %% compare
async def sequential(n: int) -> list[str]:
    return [await call_model(i) for i in range(n)]


async def concurrent(n: int) -> list[str]:
    return await asyncio.gather(*(call_model(i) for i in range(n)))


async def timed(label: str, coro) -> None:
    start = time.perf_counter()
    result = await coro
    print(f"{label:12} {time.perf_counter() - start:5.2f}s  {len(result)} replies")


# %% run
async def main() -> None:
    await timed("sequential", sequential(5))
    await timed("gather", concurrent(5))


if __name__ == "__main__":
    asyncio.run(main())
