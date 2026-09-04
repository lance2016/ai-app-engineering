"""A trace is a tree of spans. Fifty lines of Python are enough to own one.

Each span has a name, attributes, a parent, timing and a status. Attribute
names follow the OpenTelemetry GenAI semantic conventions so the same data
drops into Phoenix or Langfuse unchanged when you swap this tracer for the
real SDK. The one rule people get wrong: an exception must be *recorded* and
the status must be *set*; doing only the first leaves the span green in the UI.

Run:  uv run python lessons/18-observability/code/02_minimal_tracer.py
      INJECT_TOOL_ERROR=1 uv run python lessons/18-observability/code/02_minimal_tracer.py
      INJECT_FORGET_STATUS=1 INJECT_TOOL_ERROR=1 uv run python lessons/18-observability/code/02_minimal_tracer.py
Expect: a span tree for one agent run; with the error the tool span shows ERROR;
        with the status forgotten, the exception is there but the span still reads OK.
"""

# %% imports
import asyncio
import contextvars
import json
import os
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response

INJECT_TOOL_ERROR = os.environ.get("INJECT_TOOL_ERROR") == "1"
INJECT_FORGET_STATUS = os.environ.get("INJECT_FORGET_STATUS") == "1"


# %% span_and_tracer
@dataclass
class Span:
    name: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "UNSET"  # UNSET | OK | ERROR
    status_message: str = ""
    start: float = field(default_factory=time.time)
    end: float | None = None

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def record_exception(self, exc: BaseException) -> None:
        """Adds an event. Does NOT change status; that is a separate decision."""
        self.events.append({"name": "exception", "exception.type": type(exc).__name__, "exception.message": str(exc),
                            "exception.stacktrace": "".join(traceback.format_exception_only(exc))})

    def set_status(self, status: str, message: str = "") -> None:
        self.status, self.status_message = status, message

    @property
    def duration_ms(self) -> float:
        return round(((self.end or time.time()) - self.start) * 1000, 1)


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._current: contextvars.ContextVar[Span | None] = contextvars.ContextVar("span", default=None)

    @contextmanager
    def span(self, name: str, **attributes: Any):
        parent = self._current.get()
        span = Span(name=name, parent_id=parent.span_id if parent else None, attributes=dict(attributes))
        self.spans.append(span)
        token = self._current.set(span)
        try:
            yield span
        finally:
            span.end = time.time()
            self._current.reset(token)

    def tree(self) -> str:
        children: dict[str | None, list[Span]] = {}
        for s in self.spans:
            children.setdefault(s.parent_id, []).append(s)
        lines: list[str] = []

        def walk(parent_id: str | None, depth: int) -> None:
            for s in children.get(parent_id, []):
                flag = "" if s.status != "ERROR" else "  <-- ERROR"
                lines.append(f"{'  ' * depth}{s.name}  [{s.status}] {s.duration_ms}ms  {json.dumps(s.attributes, ensure_ascii=False)}{flag}")
                for ev in s.events:
                    lines.append(f"{'  ' * (depth + 1)}! {ev['name']}: {ev.get('exception.type')} {ev.get('exception.message')}")
                walk(s.span_id, depth + 1)

        walk(None, 0)
        return "\n".join(lines)


# %% instrumented_agent
SEARCH = ToolSpec("search", "Search.", {"type": "object", "properties": {"q": {"type": "string"}}})


def run_tool(name: str, args: dict) -> str:
    if INJECT_TOOL_ERROR:
        raise TimeoutError("search backend timed out after 5s")
    return "3 results"


async def run(tracer: Tracer) -> None:
    model = FakeAdapter(script=[tool_call_response("search", {"q": "laptops"}), ModelResponse(content="Two options.")])
    messages = [Message(role="user", content="Find laptops")]
    with tracer.span("invoke_agent support_bot", **{"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": "support_bot", "gen_ai.conversation.id": "conv_1"}) as root:
        for step in range(1, 5):
            with tracer.span("chat fake-1", **{"gen_ai.operation.name": "chat", "gen_ai.provider.name": model.name, "gen_ai.request.model": "fake-1"}) as s:  # span name = "{operation} {model}"
                reply = await model.complete(messages, tools=[SEARCH])
                s.set_attribute("gen_ai.usage.input_tokens", reply.usage.input_tokens)
                s.set_attribute("gen_ai.usage.output_tokens", reply.usage.output_tokens)
                s.set_attribute("gen_ai.response.finish_reasons", ["tool_calls" if reply.wants_tool else "stop"])
                s.set_status("OK")
            if not reply.wants_tool:
                root.set_attribute("aiapp.steps", step)
                root.set_status("OK")
                return
            messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
            for call in reply.tool_calls:
                with tracer.span(f"execute_tool {call.name}", **{"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": call.name, "gen_ai.tool.call.id": call.id, "gen_ai.tool.call.arguments": json.dumps(call.arguments)}) as t:
                    try:
                        result = run_tool(call.name, call.arguments)
                        t.set_attribute("gen_ai.tool.call.result", result)
                        t.set_status("OK")
                    except Exception as exc:  # noqa: BLE001 - we want every failure on the span
                        t.record_exception(exc)
                        if not INJECT_FORGET_STATUS:
                            t.set_status("ERROR", str(exc))  # both calls, or the UI shows a green span with a hidden exception
                        result = f"error: {exc}"
                messages.append(Message(role="tool", tool_call_id=call.id, content=result, is_error=result.startswith("error")))
        root.set_status("ERROR", "step limit")


# %% run
async def main() -> None:
    tracer = Tracer()
    await run(tracer)
    print(tracer.tree())
    errors = [s for s in tracer.spans if s.status == "ERROR"]
    with_exc = [s for s in tracer.spans if s.events]
    print(f"\nspans={len(tracer.spans)} status=ERROR:{len(errors)} with exception event:{len(with_exc)}")
    if with_exc and not errors:
        print("!! exception recorded but no span is ERROR: this is the bug the UI will hide from you")


if __name__ == "__main__":
    asyncio.run(main())
