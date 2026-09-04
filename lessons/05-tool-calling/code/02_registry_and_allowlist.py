"""Fact #1 of a successful tool call: the model picked a tool that exists
and that this request is allowed to use.

Tools live in a registry. A call to an unknown name is answered with an
error result, never executed. Each request carries an allowlist, so a
read-only context cannot reach side-effecting tools even if they are
registered.

Run:  uv run python lessons/05-tool-calling/code/02_registry_and_allowlist.py
      INJECT_UNKNOWN_TOOL=1 uv run python lessons/05-tool-calling/code/02_registry_and_allowlist.py
Expect: the hallucinated `delete_user_data` is rejected with an error result;
        the model then falls back to `search_docs`, which is allowed.
"""

# %% imports
import asyncio
import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aiapp import FakeAdapter, Message, ModelResponse, ToolCall, ToolSpec, tool_call_response

INJECT_UNKNOWN_TOOL = os.environ.get("INJECT_UNKNOWN_TOOL") == "1"


# %% Tool
@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Callable[[dict[str, Any]], str]
    has_side_effects: bool


# %% ToolRegistry
class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.spec.name] = tool

    def specs(self, allowlist: frozenset[str]) -> list[ToolSpec]:
        """Only advertise what this request may use. The model cannot pick what it cannot see."""
        return [t.spec for name, t in self._tools.items() if name in allowlist]

    def dispatch(self, call: ToolCall, allowlist: frozenset[str]) -> Message:
        tool = self._tools.get(call.name)
        if tool is None:
            return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"unknown tool: {call.name}")
        if call.name not in allowlist:
            return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"tool not allowed here: {call.name}")
        return Message(role="tool", tool_call_id=call.id, content=tool.handler(call.arguments))


# %% build_registry
def build_registry() -> ToolRegistry:
    reg = ToolRegistry()
    reg.register(Tool(
        ToolSpec("search_docs", "Search the knowledge base.", {"type": "object", "properties": {"query": {"type": "string"}}}),
        lambda a: f"3 docs match {a.get('query')!r}",
        has_side_effects=False,
    ))
    reg.register(Tool(
        ToolSpec("delete_doc", "Delete a document by id.", {"type": "object", "properties": {"doc_id": {"type": "string"}}}),
        lambda a: f"deleted {a.get('doc_id')}",
        has_side_effects=True,
    ))
    return reg


# %% build_script
def build_script() -> list[ModelResponse]:
    search = tool_call_response("search_docs", {"query": "refund policy"})
    final = ModelResponse(content="Found the refund policy in 3 documents.")
    if not INJECT_UNKNOWN_TOOL:
        return [search, final]
    hallucinated = tool_call_response("delete_user_data", {"user_id": "u_42"})  # not registered anywhere
    return [hallucinated, search, final]


# %% main
async def main() -> None:
    registry = build_registry()
    read_only = frozenset({"search_docs"})  # this request may not delete anything
    model = FakeAdapter(script=build_script())
    messages = [Message(role="user", content="Find the refund policy.")]
    for _ in range(5):
        reply = await model.complete(messages, tools=registry.specs(read_only))
        if not reply.wants_tool:
            print(f"assistant: {reply.content}")
            return
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            result = registry.dispatch(call, read_only)
            print(f"tool {call.name} -> [{'ERROR' if result.is_error else 'ok'}] {result.content}")
            messages.append(result)


# %% run
if __name__ == "__main__":
    asyncio.run(main())
