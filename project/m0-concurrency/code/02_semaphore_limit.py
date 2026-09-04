"""Twenty calls, but the provider allows four in flight.

Run:  uv run python project/m0-concurrency/code/02_semaphore_limit.py
Expect: unlimited finishes in ~1 round; limit=4 takes ~5 rounds; the peak
        in-flight count never exceeds the limit.
"""

# %% imports
import asyncio
import time

LATENCY = 0.1
in_flight = 0
peak = 0


# %% fake_call
async def call_model(i: int) -> int:
    global in_flight, peak
    in_flight += 1
    peak = max(peak, in_flight)
    await asyncio.sleep(LATENCY)
    in_flight -= 1
    return i


# %% limited
async def limited(n: int, limit: int) -> None:
    global peak
    peak = 0
    sem = asyncio.Semaphore(limit)

    async def one(i: int) -> int:
        async with sem:
            return await call_model(i)

    start = time.perf_counter()
    await asyncio.gather(*(one(i) for i in range(n)))
    print(f"limit={limit:<3} {time.perf_counter() - start:5.2f}s  peak in-flight={peak}")


# %% run
async def main() -> None:
    await limited(20, limit=100)
    await limited(20, limit=4)


if __name__ == "__main__":
    asyncio.run(main())
