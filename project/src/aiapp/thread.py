"""A thread is an append-only log of events. Everything else is derived from it.

This follows 12-factor-agents factor 5 (unify execution and business state)
and factor 12 (the agent as a stateless reducer): the messages sent to the
model, the run status and the pending tool calls are all *folds* over the
event list. Persisting a thread means persisting the list; resuming means
loading it and continuing the fold.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from aiapp.adapters.base import Message, ToolCall


@dataclass(frozen=True)
class Event:
    type: str
    data: dict[str, Any] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)


@dataclass
class Thread:
    thread_id: str = field(default_factory=lambda: f"thr_{uuid.uuid4().hex[:8]}")
    events: list[Event] = field(default_factory=list)

    # ---- writing -----------------------------------------------------------
    def append(self, type: str, **data: Any) -> Event:
        event = Event(type=type, data=data)
        self.events.append(event)
        return event

    # ---- derived views (the "reducer") ---------------------------------------
    def to_messages(self) -> list[Message]:
        """What the model should see. Runtime-only events are skipped."""
        messages: list[Message] = []
        for e in self.events:
            if e.type == "user_message":
                messages.append(Message(role="user", content=e.data["content"]))
            elif e.type == "assistant_message":
                calls = tuple(ToolCall(**c) for c in e.data.get("tool_calls", []))
                messages.append(Message(role="assistant", content=e.data.get("content", ""), tool_calls=calls))
            elif e.type == "tool_result":
                messages.append(Message(role="tool", tool_call_id=e.data["tool_call_id"], content=e.data["content"], is_error=e.data.get("is_error", False)))
            elif e.type == "human_input":
                # The human's answer *is* the result of the request_human_input call.
                messages.append(Message(role="tool", tool_call_id=e.data["tool_call_id"], content=e.data["content"]))
        return messages

    def status(self) -> str:
        for e in reversed(self.events):
            if e.type == "run_finished":
                return "finished"
            if e.type == "run_failed":
                return "failed"
            if e.type == "human_input_requested":
                return "paused"
            if e.type == "human_input":
                return "running"
        return "running" if self.events else "new"

    def pending_tool_calls(self) -> list[ToolCall]:
        """Tool calls the model asked for that have no recorded result yet."""
        answered = {e.data["tool_call_id"] for e in self.events if e.type in ("tool_result", "human_input")}
        pending: list[ToolCall] = []
        for e in self.events:
            if e.type == "assistant_message":
                pending.extend(ToolCall(**c) for c in e.data.get("tool_calls", []) if c["id"] not in answered)
        return pending

    def steps(self) -> int:
        return sum(1 for e in self.events if e.type == "assistant_message")

    # ---- persistence -------------------------------------------------------
    def to_json(self) -> str:
        return json.dumps({"thread_id": self.thread_id, "events": [asdict(e) for e in self.events]}, ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, text: str) -> "Thread":
        raw = json.loads(text)
        return cls(thread_id=raw["thread_id"], events=[Event(**e) for e in raw["events"]])

    def save(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "Thread":
        return cls.from_json(path.read_text(encoding="utf-8"))


def tool_calls_as_data(calls: tuple[ToolCall, ...]) -> list[dict[str, Any]]:
    return [{"id": c.id, "name": c.name, "arguments": c.arguments} for c in calls]
