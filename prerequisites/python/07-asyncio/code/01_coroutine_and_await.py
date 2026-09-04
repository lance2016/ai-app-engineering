"""A coroutine does nothing until something awaits it.

Run:  uv run python prerequisites/python/07-asyncio/code/01_coroutine_and_await.py
Expect: calling the function prints nothing and returns a coroutine object;
        asyncio.run drives it and the greeting appears.
"""

# %% imports
import asyncio


# %% define
async def greet(name: str) -> str:
    await asyncio.sleep(0.1)  # pretend to wait for a network reply
    return f"hello, {name}"


# %% call_without_await
thing = greet("Ada")
print(type(thing).__name__, "- nothing ran yet")
thing.close()  # avoid the 'never awaited' warning


# %% run_it
async def main() -> None:
    result = await greet("Ada")  # await hands control to the loop while sleeping
    print(result)


asyncio.run(main())
