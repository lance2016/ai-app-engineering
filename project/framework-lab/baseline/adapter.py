"""The reference implementation: M3's plain-Python runtime behind the lab protocol.

Durability here is lesson 07's JSON file per thread (a stand-in for M2's PostgreSQL),
so a 'process restart' is a new adapter over the same directory.
"""

import json
from pathlib import Path

from aiapp import Thread
from aiapp.runtime import Budget, ContextBuilder, RunContext, ToolRegistry, ToolRunner, run_agent
from aiapp.runtime.turn import Delta
from aiapp.storage.memory import InMemoryKeyValueStore
from labkit.protocol import LabEvent, LabRuntime, LabWorld, RunOutcome

SYSTEM = "You are a document workspace assistant."


class BaselineRuntime(LabRuntime):
    name = "baseline (aiapp.runtime)"

    def __init__(self, world: LabWorld, max_steps: int = 6):
        self.world = world
        self.registry = ToolRegistry()
        world.docs.register_into(self.registry)
        self.runner = ToolRunner(self.registry, InMemoryKeyValueStore(), retry_base_delay_s=0.001)
        self.max_steps = max_steps
        self.dir = world.workdir / "baseline"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, thread_id: str) -> Path:
        return self.dir / f"{thread_id}.json"

    def _load(self, thread_id: str) -> Thread:
        path = self._path(thread_id)
        return Thread.load(path) if path.exists() else Thread(thread_id=thread_id)

    async def _run(self, thread: Thread, user_content: str | None) -> RunOutcome:
        ctx = RunContext(tenant_id="lab", thread_id=thread.thread_id, allowlist=self.registry.names())
        events: list[LabEvent] = []
        try:
            async for item in run_agent(thread, self.world.model, self.runner, ctx=ctx, budget=Budget(max_steps=self.max_steps), context=ContextBuilder(SYSTEM), timeout_s=2.0, user_content=user_content):
                if not isinstance(item, Delta):
                    events.append(LabEvent(item.type, dict(item.data)))
                    thread.save(self._path(thread.thread_id))  # checkpoint per step
        except Exception as exc:  # first-chunk timeout / provider error surface as exceptions in aiapp
            thread.save(self._path(thread.thread_id))
            return RunOutcome("failed", events, detail=f"{type(exc).__name__}: {exc}")
        status = thread.status()
        last = thread.events[-1]
        if status == "paused":
            pending = {"kind": last.data.get("kind"), "tool": last.data.get("tool"), "arguments": last.data.get("arguments"), "question": last.data.get("question"), "id": last.data.get("confirm_tool_call_id") or last.data.get("tool_call_id")}
            return RunOutcome("paused", events, pending=pending)
        if status == "failed":
            return RunOutcome("failed", events, detail=str(last.data.get("reason")))
        return RunOutcome("finished", events, answer=last.data.get("answer"))

    async def start(self, thread_id: str, user_content: str) -> RunOutcome:
        thread = self._load(thread_id)
        if thread.status() == "paused":
            return RunOutcome("rejected", detail="thread is waiting for human input")
        return await self._run(thread, user_content)

    async def resume(self, thread_id: str, *, approved: bool | None = None, answer: str | None = None) -> RunOutcome:
        thread = self._load(thread_id)
        pending = thread.events[-1].data
        if approved is not None:
            thread.append("human_input", confirm_tool_call_id=pending["confirm_tool_call_id"], approved=approved)
        else:
            thread.append("human_input", tool_call_id=pending["tool_call_id"], content=answer or "")
        thread.save(self._path(thread_id))
        return await self._run(thread, None)

    async def history(self, thread_id: str) -> list[LabEvent]:
        return [LabEvent(e.type, dict(e.data)) for e in self._load(thread_id).events]

    async def close(self) -> None:
        return None


async def make_runtime(world: LabWorld) -> LabRuntime:
    return BaselineRuntime(world)
