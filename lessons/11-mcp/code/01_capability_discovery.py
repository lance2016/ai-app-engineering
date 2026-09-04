"""Fact one about MCP: the client learns what a server offers at runtime, not at compile time.

The lifecycle is initialize -> initialized -> normal operation. Only after
that may the client ask tools/list and resources/list. The same server
started with --read-only advertises fewer tools: what is not advertised
cannot be called (compare lesson 05's allowlist at the "tell the model" step).

Run:  uv run python lessons/11-mcp/code/01_capability_discovery.py
Expect: the handshake, then two capability listings, the second one without delete_note.
"""

# %% imports
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from toy_mcp.client import ToyMcpClient  # noqa: E402


# %% discover
def discover(*server_args: str) -> None:
    with ToyMcpClient(*server_args) as client:
        info = client.initialize()
        print(f"server={info['serverInfo']['name']} v{info['serverInfo']['version']} protocol={info['protocolVersion']}")
        print(f"capabilities={json.dumps(info['capabilities'])}")
        tools = client.request("tools/list")["tools"]
        print(f"tools ({' '.join(server_args) or 'default'}): {[t['name'] for t in tools]}")
        for t in tools:
            print(f"  {t['name']:14} {t['description']}  required={t['inputSchema'].get('required')}")
        resources = client.request("resources/list")["resources"]
        print(f"resources: {[r['uri'] for r in resources]}")
        note = client.request("resources/read", {"uri": resources[0]["uri"]})
        print(f"read {resources[0]['uri']!r} -> {note['contents'][0]['text'].splitlines()[0]!r} ...")


# %% run
def main() -> None:
    discover()
    print("---")
    discover("--read-only")
    print("---")
    with ToyMcpClient() as client:
        try:
            client.request("tools/list")  # before initialize: the server must refuse
        except RuntimeError as exc:
            print(f"before initialize -> {exc}")


if __name__ == "__main__":
    main()
