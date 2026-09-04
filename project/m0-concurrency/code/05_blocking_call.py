"""A single synchronous sleep freezes every other coroutine.

Run:  uv run python project/m0-concurrency/code/05_blocking_call.py
      INJECT_BLOCKING=1 uv run python project/m0-concurrency/code/05_blocking_call.py
Expect: normally the batch takes ~0.5s (the legacy call overlaps the others).
        With injection one coroutine calls time.sleep and the batch takes ~1.0s,
        because nothing else runs while the loop is held. to_thread restores ~0.5s.
"""

# %% imports
import asyncio
import os
import time

INJECT_BLOCKING = os.environ.get("INJECT_BLOCKING") == "1"


# %% calls
async def call_model(i: int) -> int:
    await asyncio.sleep(0.5)
    return i


async def legacy_sdk_call() -> str:
    """Pretend an old SDK only offers a blocking method."""
    if INJECT_BLOCKING:
        time.sleep(0.5)  # blocks the event loop: nothing else runs
    else:
        await asyncio.sleep(0.5)  # cooperative: others keep running
    return "legacy ok"


async def fixed_legacy_call() -> str:
    return await asyncio.to_thread(time.sleep, 0.5) or "legacy ok (in a thread)"


# %% run
async def batch(label: str, legacy) -> None:
    start = time.perf_counter()
    await asyncio.gather(legacy(), *(call_model(i) for i in range(5)))
    print(f"{label:34} {time.perf_counter() - start:5.2f}s")


async def main() -> None:
    await batch("legacy call as written", legacy_sdk_call)
    if INJECT_BLOCKING:
        await batch("legacy call via asyncio.to_thread", fixed_legacy_call)


if __name__ == "__main__":
    asyncio.run(main())
