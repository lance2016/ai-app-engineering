"""gather and TaskGroup both run things concurrently; they differ on failure.

Run:  uv run python prerequisites/python/07-asyncio/code/03_gather_vs_taskgroup.py
Expect: with gather the slow job still finishes after the fast one fails;
        with TaskGroup the slow job is cancelled as soon as one fails.
"""

# %% imports
import asyncio


# %% jobs
async def fails_fast() -> None:
    await asyncio.sleep(0.1)
    raise RuntimeError("boom")


async def slow(label: str) -> None:
    try:
        await asyncio.sleep(0.5)
        print(f"  [{label}] slow job finished")
    except asyncio.CancelledError:
        print(f"  [{label}] slow job was cancelled")
        raise


# %% gather
async def with_gather() -> None:
    try:
        await asyncio.gather(fails_fast(), slow("gather"))
    except RuntimeError as exc:
        print(f"gather raised {exc!r} but did not cancel the other job")
        await asyncio.sleep(0.5)  # let the slow job print its line


# %% taskgroup
async def with_taskgroup() -> None:
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(fails_fast())
            tg.create_task(slow("taskgroup"))
    except* RuntimeError as eg:
        print(f"TaskGroup raised {eg.exceptions[0]!r} and cancelled the rest")


# %% run
async def main() -> None:
    await with_gather()
    print()
    await with_taskgroup()


asyncio.run(main())
