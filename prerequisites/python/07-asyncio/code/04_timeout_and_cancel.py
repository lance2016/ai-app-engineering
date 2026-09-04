"""Timeouts cancel the awaited work; finally blocks are where cleanup happens.

Run:  uv run python prerequisites/python/07-asyncio/code/04_timeout_and_cancel.py
Expect: the slow call is cut off at 0.2s, its cleanup line still prints,
        and a manual cancel() shows the same path.
"""

# %% imports
import asyncio


# %% resource_holding_job
async def fetch_with_connection(label: str) -> str:
    print(f"  [{label}] connection opened")
    try:
        await asyncio.sleep(1.0)  # too slow
        return "data"
    finally:
        print(f"  [{label}] connection closed")  # runs on success, error AND cancellation


# %% timeout
async def with_timeout() -> None:
    try:
        async with asyncio.timeout(0.2):
            await fetch_with_connection("timeout")
    except TimeoutError:
        print("timed out after 0.2s")


# %% manual_cancel
async def with_cancel() -> None:
    task = asyncio.create_task(fetch_with_connection("cancel"))
    await asyncio.sleep(0.1)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("task cancelled by caller")


# %% run
async def main() -> None:
    await with_timeout()
    print()
    await with_cancel()


asyncio.run(main())
