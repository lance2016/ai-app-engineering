"""time.sleep blocks the whole program; asyncio.sleep lets other work run.

Run:  uv run python prerequisites/python/07-asyncio/code/02_blocking_vs_async.py
Expect: the blocking version takes ~0.9s for three jobs, the async version ~0.3s.
"""

# %% imports
import asyncio
import time


# %% blocking
async def blocking_job(i: int) -> None:
    time.sleep(0.3)  # the event loop is frozen while this runs
    print(f"  blocking job {i} done")


# %% async
async def async_job(i: int) -> None:
    await asyncio.sleep(0.3)  # gives the loop a chance to run other jobs
    print(f"  async job {i} done")


# %% compare
async def main() -> None:
    for label, job in (("time.sleep", blocking_job), ("asyncio.sleep", async_job)):
        t0 = time.perf_counter()
        await asyncio.gather(job(1), job(2), job(3))
        print(f"{label}: {time.perf_counter() - t0:.2f}s\n")


asyncio.run(main())
