"""The contract every implementation adapts to, so one scenario suite can drive them all.

Events use the lesson-07 vocabulary (user_message, run_started, assistant_message,
tool_result, human_input_requested, human_input, run_finished, run_failed). Each
adapter translates its framework's native objects into these; the translation
itself is part of what the lab compares.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from aiapp import FakeAdapter
from aiapp.tools.demo import DocStore

Status = Literal["finished", "paused", "failed", "rejected"]


@dataclass(frozen=True)
class LabEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class RunOutcome:
    status: Status
    events: list[LabEvent] = field(default_factory=list)
    answer: str | None = None
    pending: dict[str, Any] | None = None  # {"kind": "confirmation", "tool": ..., "arguments": ...} or {"kind": "question", "question": ...}
    detail: str = ""  # framework-native explanation for failed / rejected

    def tool_results(self) -> list[LabEvent]:
        return [e for e in self.events if e.type == "tool_result"]

    def tools_ran(self) -> list[str]:
        return [e.data.get("name", "") for e in self.tool_results() if not e.data.get("is_error")]


class NotSupported(Exception):
    """The framework cannot express this scenario without leaving its abstractions. Recorded on the scorecard."""


class LabRuntime(Protocol):
    name: str

    async def start(self, thread_id: str, user_content: str) -> RunOutcome:
        """Begin a run on a (new or existing) thread. Returns when the run finishes, pauses or fails.
        Must return status 'rejected' if the thread is currently waiting for human input (double texting: reject)."""
        ...

    async def resume(self, thread_id: str, *, approved: bool | None = None, answer: str | None = None) -> RunOutcome:
        """Answer the pending confirmation (approved) or question (answer) and continue from the checkpoint."""
        ...

    async def history(self, thread_id: str) -> list[LabEvent]:
        """What this runtime instance can reconstruct from durable storage alone."""
        ...

    async def close(self) -> None: ...


@dataclass
class LabWorld:
    """Everything outside the process: the (fake) model API, the document system, and durable storage on disk.
    A 'process restart' in the scenarios means: close the runtime, build a new one over the same world."""

    workdir: Path
    model: FakeAdapter
    docs: DocStore
