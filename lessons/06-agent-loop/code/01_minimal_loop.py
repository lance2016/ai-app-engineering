"""The smallest honest agent loop: decide, act, observe, until a stop condition.

The model decides the next step. The runtime executes tools, appends results,
and owns every stop condition. A step cap is the first of them: a model that
keeps calling tools forever must not take the process down with it.

Run:  uv run python lessons/06-agent-loop/code/01_minimal_loop.py
      INJECT_ENDLESS=1 uv run python lessons/06-agent-loop/code/01_minimal_loop.py
Expect: normally two tool calls then an answer with stop_reason=finished.
        With injection the model never stops asking; the loop exits with stop_reason=step_limit.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass, field
from enum import StrEnum

from aiapp import FakeAdapter, Message, ModelAdapter, ModelResponse, ToolCall, ToolSpec, tool_call_response

INJECT_ENDLESS = os.environ.get("INJECT_ENDLESS") == "1"


# %% types
class StopReason(StrEnum):
    FINISHED = "finished"  # the model answered without asking for a tool
    STEP_LIMIT = "step_limit"  # the runtime refused to continue


@dataclass
class RunResult:
    stop_reason: StopReason
    answer: str = ""
    steps: int = 0
    messages: list[Message] = field(default_factory=list)


# %% tools
TOOLS = {
    "list_files": (ToolSpec("list_files", "List files in the workspace.", {"type": "object", "properties": {}}), lambda a: "notes.md, todo.md"),
    "read_file": (ToolSpec("read_file", "Read one file.", {"type": "object", "properties": {"name": {"type": "string"}}}), lambda a: f"contents of {a.get('name')}: buy milk"),
}


def run_tool(call: ToolCall) -> Message:
    entry = TOOLS.get(call.name)
    if entry is None:
        return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"unknown tool: {call.name}")
    return Message(role="tool", tool_call_id=call.id, content=entry[1](call.arguments))


# %% run_agent
async def run_agent(model: ModelAdapter, goal: str, *, max_steps: int) -> RunResult:
    """One iteration = one model call plus the tool calls it asked for."""
    messages = [Message(role="user", content=goal)]
    specs = [spec for spec, _ in TOOLS.values()]
    for step in range(1, max_steps + 1):
        reply = await model.complete(messages, tools=specs)
        if not reply.wants_tool:
            return RunResult(StopReason.FINISHED, answer=reply.content, steps=step, messages=messages)
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            result = run_tool(call)
            print(f"step {step}: {call.name}({call.arguments}) -> {result.content}")
            messages.append(result)
    return RunResult(StopReason.STEP_LIMIT, steps=max_steps, messages=messages)


# %% script
def build_script() -> list[ModelResponse]:
    if INJECT_ENDLESS:
        return [tool_call_response("list_files", {}) for _ in range(50)]  # never answers
    return [
        tool_call_response("list_files", {}),
        tool_call_response("read_file", {"name": "todo.md"}),
        ModelResponse(content="Your todo list says: buy milk."),
    ]


# %% run
async def main() -> None:
    result = await run_agent(FakeAdapter(script=build_script()), "What's on my todo list?", max_steps=5)
    print(f"stop_reason={result.stop_reason} steps={result.steps} answer={result.answer!r}")


if __name__ == "__main__":
    asyncio.run(main())
