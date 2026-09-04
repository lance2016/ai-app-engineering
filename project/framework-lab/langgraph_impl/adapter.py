"""LangGraph behind the lab protocol. Durability = AsyncSqliteSaver on a file in the world's workdir."""

import aiosqlite
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.errors import GraphRecursionError
from langgraph.types import Command

from labkit.protocol import LabEvent, LabRuntime, LabWorld, RunOutcome
from langgraph_impl.agent import build_graph
from langgraph_impl.fake_chat_model import ScriptedChatModel

MAX_STEPS = 6


def _events(messages: list, tool_names: dict[str, str]) -> list[LabEvent]:
    out: list[LabEvent] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append(LabEvent("user_message", {"content": str(m.content)}))
        elif isinstance(m, AIMessage):
            for c in m.tool_calls:
                tool_names[c["id"]] = c["name"]
            out.append(LabEvent("assistant_message", {"content": str(m.content), "tool_calls": [{"id": c["id"], "name": c["name"], "arguments": c["args"]} for c in m.tool_calls]}))
        elif isinstance(m, ToolMessage):
            out.append(LabEvent("tool_result", {"tool_call_id": m.tool_call_id, "name": m.name or tool_names.get(m.tool_call_id, ""), "content": str(m.content), "is_error": m.status == "error"}))
    return out


class LangGraphRuntime(LabRuntime):
    name = "langgraph"

    def __init__(self, world: LabWorld):
        self.world = world
        self.conn: aiosqlite.Connection | None = None
        self.graph = None

    async def open(self) -> "LangGraphRuntime":
        (self.world.workdir / "langgraph").mkdir(parents=True, exist_ok=True)
        self.conn = await aiosqlite.connect(self.world.workdir / "langgraph" / "checkpoints.sqlite")
        saver = AsyncSqliteSaver(self.conn)
        await saver.setup()
        self.graph = build_graph(ScriptedChatModel(fake=self.world.model), self.world.docs, saver)
        return self

    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}, "recursion_limit": 2 * MAX_STEPS + 1}

    async def _pending(self, thread_id: str) -> dict | None:
        state = await self.graph.aget_state(self._config(thread_id))
        for task in state.tasks:
            for intr in task.interrupts:
                return dict(intr.value)
        return None

    async def _outcome(self, thread_id: str, before: int, error: str | None = None) -> RunOutcome:
        state = await self.graph.aget_state(self._config(thread_id))
        all_events = _events(state.values.get("messages", []), {})
        events = all_events[before:]
        if error is not None:
            events.append(LabEvent("run_failed", {"reason": error}))
            return RunOutcome("failed", events, detail=error)
        pending = await self._pending(thread_id)
        if pending is not None:
            events.append(LabEvent("human_input_requested", pending))
            return RunOutcome("paused", events, pending=pending)
        answer = next((e.data["content"] for e in reversed(all_events) if e.type == "assistant_message" and not e.data["tool_calls"]), None)
        events.append(LabEvent("run_finished", {"answer": answer}))
        return RunOutcome("finished", events, answer=answer)

    async def _count(self, thread_id: str) -> int:
        state = await self.graph.aget_state(self._config(thread_id))
        return len(state.values.get("messages", []))

    async def _invoke(self, thread_id: str, payload) -> RunOutcome:
        before = await self._count(thread_id)
        try:
            await self.graph.ainvoke(payload, self._config(thread_id))
        except GraphRecursionError as exc:
            return await self._outcome(thread_id, before, error=f"recursion_limit: {exc}")
        except Exception as exc:  # noqa: BLE001
            return await self._outcome(thread_id, before, error=f"{type(exc).__name__}: {exc}")
        return await self._outcome(thread_id, before)

    async def start(self, thread_id: str, user_content: str) -> RunOutcome:
        if await self._pending(thread_id) is not None:
            return RunOutcome("rejected", detail="graph is interrupted and waiting for Command(resume=...)")
        return await self._invoke(thread_id, {"messages": [HumanMessage(content=user_content)], "steps": 0})

    async def resume(self, thread_id: str, *, approved: bool | None = None, answer: str | None = None) -> RunOutcome:
        value = approved if approved is not None else (answer or "")
        out = await self._invoke(thread_id, Command(resume=value))
        out.events.insert(0, LabEvent("human_input", {"approved": approved} if approved is not None else {"content": answer}))
        return out

    async def history(self, thread_id: str) -> list[LabEvent]:
        state = await self.graph.aget_state(self._config(thread_id))
        return _events(state.values.get("messages", []), {})

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()
            self.conn = None


async def make_runtime(world: LabWorld) -> LabRuntime:
    return await LangGraphRuntime(world).open()
