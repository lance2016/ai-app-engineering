"""The M3 agent end to end, offline: search, read, a paused side effect, approval, a skill, all in one thread.

The fake model follows a script; everything else is the real runtime:
``ToolRegistry`` + ``ToolRunner`` guards, ``run_agent`` loop and budget,
``SkillLoader`` progressive loading, an in-memory store with per-step
checkpoints. Watch the event types: they are exactly what the HTTP API streams.

Run:  uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
      INJECT_FLAKY_SEARCH=1 uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
      USER_DECISION=no uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
Expect: run 1 pauses at the delete confirmation; run 2 (the "approval request")
        executes the delete exactly once and finishes. With the injection the
        first search fails transiently and is retried (attempts=2). With
        USER_DECISION=no the delete is declined and the doc stays.
"""

# %% imports
import asyncio
import os
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, Thread, tool_call_response
from aiapp.runtime import Budget, ContextBuilder, RunContext, SkillLoader, ToolRegistry, ToolRunner, run_agent
from aiapp.runtime.turn import Delta
from aiapp.storage import InMemoryKeyValueStore, InMemoryThreadStore, flush
from aiapp.tools.demo import DocStore

INJECT_FLAKY_SEARCH = os.environ.get("INJECT_FLAKY_SEARCH") == "1"
USER_DECISION = os.environ.get("USER_DECISION", "yes")
SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"


# %% script
def script(approved: bool) -> list[ModelResponse]:
    return [
        tool_call_response("search_docs", {"query": "draft"}, call_id="c1"),
        tool_call_response("delete_doc", {"doc_id": "doc_returns_draft", "reason": "draft"}, call_id="c2"),
        # the run pauses here; the next responses are consumed after the human decides
        tool_call_response("load_skill", {"name": "expense-report"}, call_id="c3"),
        ModelResponse(content="Draft removed; expense skill loaded for later." if approved else "Left the draft in place as you asked."),
    ]


# %% wiring
async def main() -> None:
    docs = DocStore(fail_next_searches=1 if INJECT_FLAKY_SEARCH else 0)
    registry = ToolRegistry()
    docs.register_into(registry)
    skills = SkillLoader(SKILLS_DIR).discover(registry.names())
    skills.register_into(registry)
    kv, store = InMemoryKeyValueStore(), InMemoryThreadStore()
    runner = ToolRunner(registry, kv, retry_base_delay_s=0.01)
    model = FakeAdapter(script=script(USER_DECISION == "yes"), chunk_size=12)
    context = ContextBuilder("You are a document workspace assistant.", skill_catalog=skills.catalog())

    thread = await store.create("tenant-demo")
    ctx = RunContext(tenant_id="tenant-demo", thread_id=thread.thread_id, allowlist=registry.names())

    async def run(label: str, user_content: str | None) -> None:
        persisted = len(thread.events)
        print(f"\n== {label}")
        async for item in run_agent(thread, model, runner, ctx=ctx, budget=Budget(max_steps=8), context=context, skills=skills, timeout_s=5, user_content=user_content):
            if isinstance(item, Delta):
                continue
            extra = {k: v for k, v in item.data.items() if k in ("name", "route", "attempts", "kind", "tool", "reason", "answer")}
            print(f"  {item.type:24} {extra}")
            persisted = await flush(store, thread, persisted)  # checkpoint per step, like the API does

    await run("request 1: the user asks", "Find the returns draft and delete it, then get ready to review expenses.")
    assert thread.status() == "paused" and docs.deleted == []
    pending = thread.events[-1].data
    print(f"\npaused for confirmation of {pending['tool']}({pending['arguments']}); user says {USER_DECISION!r}")

    # "another request, maybe hours later": load from the store, record the decision, continue the same fold
    reloaded = await store.load(thread.thread_id, tenant_id="tenant-demo")
    reloaded.append("human_input", confirm_tool_call_id=pending["confirm_tool_call_id"], approved=USER_DECISION == "yes")
    await flush(store, reloaded, len(reloaded.events) - 1)
    thread.events[:] = reloaded.events
    await run("request 2: the human decided", None)

    final = await store.load(thread.thread_id, tenant_id="tenant-demo")
    print(f"\nstatus={final.status()} events={len(final.events)} deleted={docs.deleted}")
    assert final.status() == "finished"
    assert (docs.deleted == ["doc_returns_draft"]) == (USER_DECISION == "yes")


if __name__ == "__main__":
    asyncio.run(main())
