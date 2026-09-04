"""Fact two: an MCP server's tool list is the server's offer, not your policy.

The client wraps discovered tools into the runtime's own ToolSpec objects and
applies its own allowlist before anything reaches the model. Tool failures
come back as results with isError, exactly like lesson 05's error results.

Run:  uv run python lessons/11-mcp/code/02_tool_call_and_allowlist.py
      INJECT_WRITE_CALL=1 uv run python lessons/11-mcp/code/02_tool_call_and_allowlist.py
Expect: search_notes round-trips through the server. With injection the
        model asks for delete_note, which the client never forwards.
"""

# %% imports
import json
import os
import sys
from pathlib import Path

from aiapp import FakeAdapter, Message, ModelResponse, ToolCall, ToolSpec, tool_call_response

sys.path.insert(0, str(Path(__file__).parent))
from toy_mcp.client import ToyMcpClient  # noqa: E402

INJECT_WRITE_CALL = os.environ.get("INJECT_WRITE_CALL") == "1"
ALLOWLIST = frozenset({"search_notes"})  # this request may not delete anything, whatever the server offers


# %% bridge
def specs_from_server(client: ToyMcpClient, allowlist: frozenset[str]) -> list[ToolSpec]:
    """MCP tool -> runtime ToolSpec. Only allowlisted tools are shown to the model."""
    return [
        ToolSpec(name=t["name"], description=t["description"], parameters=t["inputSchema"])
        for t in client.request("tools/list")["tools"] if t["name"] in allowlist
    ]


def dispatch(client: ToyMcpClient, call: ToolCall, allowlist: frozenset[str]) -> Message:
    if call.name not in allowlist:
        return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"tool not allowed here: {call.name}")
    try:
        res = client.request("tools/call", {"name": call.name, "arguments": call.arguments})
    except RuntimeError as exc:  # JSON-RPC error: bad params, unknown tool
        return Message(role="tool", tool_call_id=call.id, is_error=True, content=str(exc))
    text = " ".join(c["text"] for c in res["content"] if c["type"] == "text")
    return Message(role="tool", tool_call_id=call.id, is_error=res.get("isError", False), content=text)


# %% script
def build_script() -> list[ModelResponse]:
    search = tool_call_response("search_notes", {"query": "milk"})
    final = ModelResponse(content="Your todo note mentions milk.")
    if not INJECT_WRITE_CALL:
        return [search, final]
    return [tool_call_response("delete_note", {"uri": "notes://todo"}), search, final]


# %% run
def main() -> None:
    with ToyMcpClient() as client:  # server is NOT read-only: it offers delete_note
        client.initialize()
        offered = [t["name"] for t in client.request("tools/list")["tools"]]
        specs = specs_from_server(client, ALLOWLIST)
        print(f"server offers {offered}; model sees {[s.name for s in specs]}")
        model = FakeAdapter(script=build_script())
        messages = [Message(role="user", content="Do I need to buy milk?")]
        import asyncio
        for _ in range(5):
            reply = asyncio.run(model.complete(messages, tools=specs))
            if not reply.wants_tool:
                print(f"assistant: {reply.content}")
                break
            messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
            for call in reply.tool_calls:
                res = dispatch(client, call, ALLOWLIST)
                print(f"tool {call.name}({json.dumps(call.arguments)}) -> [{'ERROR' if res.is_error else 'ok'}] {res.content}")
                messages.append(res)
        # a bad-params call, straight to the server, to show the two error channels
        try:
            client.request("tools/call", {"name": "search_notes", "arguments": {}})
        except RuntimeError as exc:
            print(f"missing required param -> JSON-RPC error {exc}")
        res = client.request("tools/call", {"name": "delete_note", "arguments": {"uri": "notes://nope"}})
        print(f"tool-level failure -> isError={res['isError']} {res['content'][0]['text']!r}")


if __name__ == "__main__":
    main()
