"""Fact three: the server is another process. It can die, hang, or disappear.

A client that blocks forever on a dead server takes the agent loop with it.
This one detects EOF on the server's stdout, turns it into an error result
the model can see, and cleans up the subprocess. Reconnecting means running
the lifecycle again; discovered capabilities are not assumed to survive.

Run:  uv run python lessons/11-mcp/code/03_disconnect_handling.py
      INJECT_SERVER_CRASH=1 uv run python lessons/11-mcp/code/03_disconnect_handling.py
Expect: normally a clean call. With injection the server exits during tools/call;
        the client reports it, reconnects, and completes the call on a fresh server.
"""

# %% imports
import os
import sys
from pathlib import Path

from aiapp import Message, ToolCall

sys.path.insert(0, str(Path(__file__).parent))
from toy_mcp.client import ServerGone, ToyMcpClient  # noqa: E402

INJECT_SERVER_CRASH = os.environ.get("INJECT_SERVER_CRASH") == "1"


# %% connect
def connect(*args: str) -> ToyMcpClient:
    client = ToyMcpClient(*args, timeout=2.0)
    client.initialize()
    return client


# %% call_with_reconnect
def call(client: ToyMcpClient, tool: ToolCall) -> tuple[ToyMcpClient, Message]:
    """Try once; on a dead server, reconnect once (to a healthy server) and retry."""
    for attempt in (1, 2):
        try:
            res = client.request("tools/call", {"name": tool.name, "arguments": tool.arguments})
            return client, Message(role="tool", tool_call_id=tool.id, content=res["content"][0]["text"])
        except ServerGone as exc:
            print(f"attempt {attempt}: server gone ({exc})")
            client.close()
            if attempt == 2:
                return client, Message(role="tool", tool_call_id=tool.id, is_error=True, content="notes server unavailable")
            client = connect()  # fresh process, fresh handshake; capabilities re-discovered
            print("reconnected; re-ran initialize")
    raise AssertionError("unreachable")


# %% run
def main() -> None:
    client = connect(*(["--crash-on", "tools/call"] if INJECT_SERVER_CRASH else []))
    try:
        client, result = call(client, ToolCall(id="c1", name="search_notes", arguments={"query": "mum"}))
        print(f"result: [{'ERROR' if result.is_error else 'ok'}] {result.content}")
    finally:
        client.close()
    print("subprocess cleaned up")


if __name__ == "__main__":
    main()
