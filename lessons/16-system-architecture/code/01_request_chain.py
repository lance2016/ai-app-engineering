"""One request, every hop, with timings. Three shapes: sync, streamed, long task.

Each component is a small async function that appends an event and reports
how long it took. Run the same chain in three modes to see where the time goes
and what the client receives in each shape. Nothing here talks to a network;
the point is the order of the hops and who owns which piece of state.

Run:  uv run python lessons/16-system-architecture/code/01_request_chain.py
      MODE=stream uv run python lessons/16-system-architecture/code/01_request_chain.py
      MODE=task   uv run python lessons/16-system-architecture/code/01_request_chain.py
Expect: sync returns once at the end; stream emits deltas while the model runs;
        task returns a task id immediately and the work completes in the background.
"""

# %% imports
import asyncio
import os
import time
from collections.abc import AsyncIterator

from aiapp import FakeAdapter, Message, ModelResponse, Thread, ToolSpec, tool_call_response, tool_calls_as_data

MODE = os.environ.get("MODE", "sync")
SEARCH = ToolSpec("search_kb", "Search the knowledge base.", {"type": "object", "properties": {"q": {"type": "string"}}})


# %% hops
class Hop:
    """Times a component and records it on the thread as a runtime-only event."""

    def __init__(self, thread: Thread, name: str):
        self.thread, self.name = thread, name

    async def __aenter__(self):
        self.t0 = time.perf_counter()
        return self

    async def __aexit__(self, *exc):
        ms = (time.perf_counter() - self.t0) * 1000
        self.thread.append("hop", name=self.name, ms=round(ms, 1))
        print(f"  {self.name:14} {ms:6.1f} ms")


async def gateway_auth(thread: Thread, token: str) -> str:
    async with Hop(thread, "gateway/auth"):
        await asyncio.sleep(0.005)
        return "u42" if token == "valid" else ""


async def load_session(thread: Thread, user_id: str) -> None:
    async with Hop(thread, "session/load"):
        await asyncio.sleep(0.01)  # PostgreSQL: durable history
        thread.append("user_message", content="What is the refund window?")


async def retrieve(thread: Thread) -> str:
    async with Hop(thread, "retrieval"):
        await asyncio.sleep(0.02)  # pgvector + BM25
        return "Refunds within 30 days (policy/refund.md v2)"


async def call_model(thread: Thread, model: FakeAdapter, context: str) -> ModelResponse:
    async with Hop(thread, "model"):
        reply = await model.complete(thread.to_messages() + [Message(role="system", content=context)], tools=[SEARCH])
        await asyncio.sleep(0.03)
        return reply


async def persist(thread: Thread) -> None:
    async with Hop(thread, "persist"):
        await asyncio.sleep(0.008)  # write events; Redis holds only the "run in progress" flag


# %% three_shapes
async def run_sync(model: FakeAdapter) -> str:
    thread = Thread()
    user = await gateway_auth(thread, "valid")
    await load_session(thread, user)
    ctx = await retrieve(thread)
    reply = await call_model(thread, model, ctx)
    thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
    await persist(thread)
    return reply.content


async def run_stream(model: FakeAdapter) -> AsyncIterator[str]:
    thread = Thread()
    user = await gateway_auth(thread, "valid")
    await load_session(thread, user)
    ctx = await retrieve(thread)
    reply = await call_model(thread, model, ctx)
    for word in reply.content.split():  # a real adapter yields deltas; the shape is the same
        await asyncio.sleep(0.01)
        yield word + " "
    thread.append("assistant_message", content=reply.content)
    await persist(thread)


async def run_task(model: FakeAdapter) -> tuple[str, asyncio.Task]:
    """Return immediately with an id; the worker finishes and persists on its own."""
    task_id = "task_7f3a"

    async def worker() -> None:
        thread = Thread(thread_id=task_id)
        thread.append("user_message", content="Summarise all refund tickets this month.")
        ctx = await retrieve(thread)
        reply = await call_model(thread, model, ctx)
        thread.append("assistant_message", content=reply.content)
        await persist(thread)
        print(f"  [worker] {task_id} finished: {reply.content!r}")

    return task_id, asyncio.create_task(worker())


# %% run
async def main() -> None:
    model = FakeAdapter(script=[ModelResponse(content="You can request a refund within 30 days of purchase.")])
    t0 = time.perf_counter()
    print(f"mode={MODE}")
    if MODE == "sync":
        answer = await run_sync(model)
        print(f"client receives after {(time.perf_counter() - t0) * 1000:.0f} ms: {answer!r}")
    elif MODE == "stream":
        first = None
        async for delta in run_stream(model):
            first = first or (time.perf_counter() - t0) * 1000
            print(f"  delta: {delta!r}")
        print(f"first byte at {first:.0f} ms, done at {(time.perf_counter() - t0) * 1000:.0f} ms")
    elif MODE == "task":
        task_id, task = await run_task(model)
        print(f"client receives task id {task_id} after {(time.perf_counter() - t0) * 1000:.0f} ms; polls or subscribes for the result")
        await task
    else:
        raise SystemExit(f"unknown MODE {MODE!r}")


if __name__ == "__main__":
    asyncio.run(main())
