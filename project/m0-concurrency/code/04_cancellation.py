"""One task fails; TaskGroup cancels its siblings; shielded work survives.

Run:  uv run python project/m0-concurrency/code/04_cancellation.py
Expect: the failing task's error surfaces as an ExceptionGroup, the sibling
        reports it was cancelled, and the shielded audit write still completes.
"""

# %% imports
import asyncio


# %% tasks
async def flaky() -> None:
    await asyncio.sleep(0.1)
    raise RuntimeError("provider returned 500")


async def sibling() -> None:
    try:
        await asyncio.sleep(1.0)
    except asyncio.CancelledError:
        print("  sibling: cancelled because a sibling failed")
        raise


async def audit_write() -> None:
    await asyncio.sleep(0.3)
    print("  audit: written (was shielded, so cancellation did not stop it)")


# %% run
async def main() -> None:
    audit = asyncio.shield(asyncio.create_task(audit_write()))
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(flaky())
            tg.create_task(sibling())
    except* RuntimeError as eg:
        print(f"group failed: {[str(e) for e in eg.exceptions]}")
    await audit


if __name__ == "__main__":
    asyncio.run(main())
