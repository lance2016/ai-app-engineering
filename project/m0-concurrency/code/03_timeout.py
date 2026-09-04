"""A slow call is cut off; the cleanup in `finally` still runs.

Run:  uv run python project/m0-concurrency/code/03_timeout.py
Expect: the fast call returns; the slow call raises TimeoutError after the
        budget, and its `finally` block prints that it released its resource.
"""

# %% imports
import asyncio


# %% call_with_cleanup
async def call_model(label: str, latency: float) -> str:
    print(f"  {label}: acquired connection")
    try:
        await asyncio.sleep(latency)
        return f"{label}: ok"
    finally:
        print(f"  {label}: released connection")  # runs on success AND on cancellation


# %% run
async def main() -> None:
    print(await asyncio.wait_for(call_model("fast", 0.1), timeout=0.5))
    try:
        await asyncio.wait_for(call_model("slow", 2.0), timeout=0.3)
    except TimeoutError:
        print("slow: TimeoutError after 0.3s budget")


if __name__ == "__main__":
    asyncio.run(main())
