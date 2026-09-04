"""Four failures, one trace each. Learn what each one looks like before it happens in production.

Inject a tool timeout, an empty model reply, a cost spike or a loop, then read
the span tree the way you would in Phoenix: durations, token attributes,
repeated children, error status. The tracer is a compact copy of the one in
02_minimal_tracer.py; M5 folds it into aiapp.

Run:  uv run python lessons/18-observability/code/03_failure_experiments.py
      INJECT=tool_timeout | empty_model | cost_spike | loop   (as an env var)
Expect: a span tree plus a short 'what to look at' note pointing at the tell-tale signal.
"""

# %% imports
import asyncio
import contextvars
import json
import os
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response

INJECT = os.environ.get("INJECT", "")
PRICE_PER_1K_INPUT = 0.002  # illustrative; real prices go in config with a date


# %% compact_tracer
@dataclass
class Span:
    name: str
    parent_id: str | None
    attributes: dict[str, Any] = field(default_factory=dict)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    status: str = "UNSET"
    start: float = field(default_factory=time.time)
    end: float | None = None

    @property
    def duration_ms(self) -> float:
        return round(((self.end or time.time()) - self.start) * 1000, 1)


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._cur: contextvars.ContextVar[Span | None] = contextvars.ContextVar("cur", default=None)

    @contextmanager
    def span(self, name: str, **attrs: Any):
        parent = self._cur.get()
        s = Span(name, parent.span_id if parent else None, dict(attrs))
        self.spans.append(s)
        tok = self._cur.set(s)
        try:
            yield s
        finally:
            s.end = time.time()
            self._cur.reset(tok)

    def tree(self) -> str:
        kids: dict[str | None, list[Span]] = {}
        for s in self.spans:
            kids.setdefault(s.parent_id, []).append(s)
        out: list[str] = []

        def walk(pid: str | None, d: int) -> None:
            for s in kids.get(pid, []):
                out.append(f"{'  ' * d}{s.name} [{s.status}] {s.duration_ms}ms {json.dumps(s.attributes)}")
                walk(s.span_id, d + 1)

        walk(None, 0)
        return "\n".join(out)


# %% scenario_scripts
SEARCH = ToolSpec("search", "Search.", {"type": "object", "properties": {"q": {"type": "string"}}})


def script() -> list[ModelResponse]:
    if INJECT == "loop":
        return [tool_call_response("search", {"q": "same"}) for _ in range(6)]
    if INJECT == "empty_model":
        return [ModelResponse(content="")]
    return [tool_call_response("search", {"q": "laptops"}), ModelResponse(content="done")]


async def run_tool(args: dict) -> str:
    if INJECT == "tool_timeout":
        await asyncio.sleep(0.4)
        raise TimeoutError("backend did not answer in 0.4s")
    if INJECT == "cost_spike":
        return "result row\n" * 4000  # an unpaginated tool result becomes next turn's input
    return "3 results"


# %% instrumented_run
async def run(tracer: Tracer) -> None:
    model = FakeAdapter(script=script())
    messages = [Message(role="user", content="Find laptops")]
    total_in = 0
    with tracer.span("invoke_agent support_bot", **{"gen_ai.operation.name": "invoke_agent"}) as root:
        for step in range(1, 6):
            with tracer.span("chat fake-1", **{"gen_ai.operation.name": "chat", "gen_ai.request.model": "fake-1"}) as s:
                reply = await model.complete(messages, tools=[SEARCH])
                total_in += reply.usage.input_tokens
                s.attributes.update({"gen_ai.usage.input_tokens": reply.usage.input_tokens, "gen_ai.usage.output_tokens": reply.usage.output_tokens})
                s.status = "OK"
                if not reply.wants_tool and not reply.content:
                    s.attributes["aiapp.empty_output"] = True
                    s.status = "ERROR"
            if not reply.wants_tool:
                root.status = "OK" if reply.content else "ERROR"
                break
            messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
            for call in reply.tool_calls:
                with tracer.span(f"execute_tool {call.name}", **{"gen_ai.tool.name": call.name, "aiapp.args_hash": hash(json.dumps(call.arguments, sort_keys=True)) % 10_000}) as t:
                    try:
                        result = await asyncio.wait_for(run_tool(call.arguments), timeout=0.3)
                        t.status = "OK"
                    except (TimeoutError, asyncio.TimeoutError) as exc:
                        result = f"error: {exc}"
                        t.status = "ERROR"
                        t.attributes["error.type"] = type(exc).__name__
                messages.append(Message(role="tool", tool_call_id=call.id, content=result))
        else:
            root.status = "ERROR"
            root.attributes["aiapp.stop_reason"] = "step_limit"
        root.attributes["aiapp.cost_usd"] = round(total_in / 1000 * PRICE_PER_1K_INPUT, 4)


# %% what_to_look_at
NOTES = {
    "": "healthy: one chat, one tool, one chat; all OK; cost in the root span.",
    "tool_timeout": "execute_tool span is ERROR with error.type=TimeoutError and its duration sits right at the timeout. The chat span after it is fine: the model coped, the backend did not.",
    "empty_model": "chat span is ERROR with aiapp.empty_output=true and near-zero output tokens. Nothing threw; only an attribute check catches this. With a real SDK alert on gen_ai.usage.output_tokens==0 or an unexpected finish reason.",
    "cost_spike": "the second chat span's gen_ai.usage.input_tokens is thousands, not tens, and root aiapp.cost_usd jumps. Tool results are context; an unpaginated result costs money on every later turn.",
    "loop": "five execute_tool children with the same aiapp.args_hash under one root, root ends ERROR with stop_reason=step_limit. Count identical children per trace; that is your loop detector.",
}


async def main() -> None:
    tracer = Tracer()
    await run(tracer)
    print(f"scenario: {INJECT or 'healthy'}\n")
    print(tracer.tree())
    print(f"\nwhat to look at: {NOTES[INJECT]}")


if __name__ == "__main__":
    asyncio.run(main())
