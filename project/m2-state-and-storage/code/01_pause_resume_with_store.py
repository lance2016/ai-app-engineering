"""Lesson 07's launch / pause / resume, with the thread in a ThreadStore instead of a JSON file.

The loop is the one from lessons/07 `02_pause_resume.py`. What changed: every
event goes through ``store.append(expected_seq=...)`` as soon as it exists,
so a crash at any step loses at most the step in flight, and two writers can
never interleave. With DATABASE_URL set the store is PostgreSQL and the
checkpoint survives this process; without it an in-memory store stands in
and the three "processes" below run inside one script.

Run:  uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py
      DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py
      INJECT_CRASH=1 uv run python project/m2-state-and-storage/code/01_pause_resume_with_store.py
Expect: process 1 pauses at the question, process 2 resumes with the answer and
        finishes, every tool ran exactly once. With INJECT_CRASH the first process
        dies after step 1 and the recovery run does not re-execute that tool.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, ModelResponse, Thread, ToolCall, ToolSpec, tool_call_response, tool_calls_as_data
from aiapp.storage import InMemoryThreadStore, ThreadStore, flush

INJECT_CRASH = os.environ.get("INJECT_CRASH") == "1"
DATABASE_URL = os.environ.get("DATABASE_URL")

TOOLS = [
    ToolSpec("find_restaurants", "Find restaurants.", {"type": "object", "properties": {"party": {"type": "integer"}}}),
    ToolSpec("request_human_input", "Ask the user a question and wait.", {"type": "object", "properties": {"question": {"type": "string"}}}),
    ToolSpec("book", "Book a table.", {"type": "object", "properties": {"name": {"type": "string"}}}),
]
EXECUTIONS: dict[str, int] = {}


class SimulatedCrash(Exception):
    pass


# %% tools
def execute(call: ToolCall) -> str:
    EXECUTIONS[call.name] = EXECUTIONS.get(call.name, 0) + 1
    if call.name == "find_restaurants":
        return '["Noodle House", "Sea Breeze"]'
    if call.name == "book":
        return f"booked {call.arguments['name']} for tonight"
    raise ValueError(call.name)


# %% loop
async def run(store: ThreadStore, thread: Thread, model: FakeAdapter, *, crash_after_first_tool: bool = False) -> str:
    """Continue the fold from wherever the thread is. Every append is checkpointed before the next step."""
    persisted = len(thread.events)
    for _ in range(6):
        for call in thread.pending_tool_calls():
            if call.name == "request_human_input":
                thread.append("human_input_requested", tool_call_id=call.id, question=call.arguments["question"])
                persisted = await flush(store, thread, persisted)
                return "paused"
            thread.append("tool_result", tool_call_id=call.id, content=execute(call))
            persisted = await flush(store, thread, persisted)
            if crash_after_first_tool:
                raise SimulatedCrash("died after recording step 1")
        reply = await model.complete(thread.to_messages(), tools=TOOLS)
        thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
        persisted = await flush(store, thread, persisted)
        if not reply.wants_tool:
            thread.append("run_finished", answer=reply.content)
            await flush(store, thread, persisted)
            return "finished"
    return "step_limit"


def script_from(thread: Thread, answer: str | None) -> list[ModelResponse]:
    done = {e.data.get("tool_call_id") for e in thread.events if e.type in ("tool_result", "human_input")}
    plan = [
        ("c1", tool_call_response("find_restaurants", {"party": 2}, call_id="c1")),
        ("c2", tool_call_response("request_human_input", {"question": "Noodle House or Sea Breeze?"}, call_id="c2")),
        ("c3", tool_call_response("book", {"name": answer or "?"}, call_id="c3")),
    ]
    return [r for cid, r in plan if cid not in done] + [ModelResponse(content=f"Done, {answer} is booked for two tonight.")]


# %% three processes
async def main() -> None:
    if DATABASE_URL:
        from aiapp.storage.postgres import PostgresThreadStore

        store: ThreadStore = PostgresThreadStore.from_url(DATABASE_URL)
        print(f"store: PostgreSQL ({DATABASE_URL.split('@')[-1]})")
    else:
        store = InMemoryThreadStore()
        print("store: in-memory (set DATABASE_URL to use PostgreSQL)")
    tenant = "tenant-demo"

    # process 1: launch
    thread = await store.create(tenant)
    thread.append("user_message", content="Book me a table for two tonight.")
    await flush(store, thread, 0)
    try:
        outcome = await run(store, thread, FakeAdapter(script=script_from(thread, None)), crash_after_first_tool=INJECT_CRASH)
    except SimulatedCrash as exc:
        print(f"process 1: !! {exc}")
        outcome = "crashed"
    print(f"process 1: {outcome}; executions so far {EXECUTIONS}")

    # process 2: a fresh load from the store. Nothing in memory survived.
    thread = await store.load(thread.thread_id, tenant_id=tenant)
    print(f"process 2: loaded {thread.thread_id} status={thread.status()} events={len(thread.events)} pending={[c.name for c in thread.pending_tool_calls()]}")
    if thread.status() != "paused":
        outcome = await run(store, thread, FakeAdapter(script=script_from(thread, None)))
        print(f"process 2: {outcome} (recovered without re-running find_restaurants)")
        thread = await store.load(thread.thread_id, tenant_id=tenant)

    # process 3: the human answers
    pending = thread.pending_tool_calls()[0]
    thread.append("human_input", tool_call_id=pending.id, content="Sea Breeze")
    await flush(store, thread, len(thread.events) - 1)
    outcome = await run(store, thread, FakeAdapter(script=script_from(thread, "Sea Breeze")))
    final = await store.load(thread.thread_id, tenant_id=tenant)
    print(f"process 3: {outcome}; status={final.status()} events={[e.type for e in final.events]}")
    print(f"tool executions across all processes: {EXECUTIONS}")
    assert all(n == 1 for n in EXECUTIONS.values()), "a tool ran twice"
    if hasattr(store, "dispose"):
        await store.dispose()


if __name__ == "__main__":
    asyncio.run(main())
