"""Register an MCP server's tools into the runtime's own registry (lesson 11).

The server's tools/list is an offer, not a policy: each tool becomes an ordinary
``Tool`` that the runner validates, authorizes, confirms and traces like a local
one. A dead server is a transient error: the handler reconnects once and lets the
runner's retry decide; if the server is gone for good, the model gets an error
result instead of the request failing with a 500.
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass, field

from aiapp.adapters.base import ToolSpec
from aiapp.mcp.client import ServerGone, StdioMcpClient
from aiapp.runtime.errors import TransientToolError
from aiapp.runtime.registry import Tool, ToolRegistry

log = logging.getLogger("aiapp.runtime.mcp")


@dataclass
class MCPToolSource:
    command: list[str]
    name: str = "mcp"
    client: StdioMcpClient | None = field(default=None, init=False)
    tools: list[str] = field(default_factory=list, init=False)

    @classmethod
    def from_command_line(cls, command_line: str, name: str = "mcp") -> "MCPToolSource":
        return cls(shlex.split(command_line), name=name)

    def connect(self) -> StdioMcpClient:
        self.client = StdioMcpClient(self.command)
        self.client.connect()
        return self.client

    def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None

    def register_into(self, registry: ToolRegistry) -> list[str]:
        """Discover tools/list and register each as a Tool. Side effects come from the spec's readOnlyHint, defaulting to 'yes'."""
        client = self.client or self.connect()
        self.tools = []
        for t in client.request("tools/list")["tools"]:
            read_only = bool(t.get("annotations", {}).get("readOnlyHint", False))
            spec = ToolSpec(name=t["name"], description=t["description"], parameters=t["inputSchema"])
            registry.register(Tool(spec, self._handler(t["name"]), has_side_effects=not read_only))
            self.tools.append(t["name"])
        log.info("mcp %s registered %s", self.name, self.tools)
        return self.tools

    def _handler(self, tool_name: str):
        async def call(arguments: dict) -> str:
            return await asyncio.to_thread(self._call_blocking, tool_name, arguments)

        return call

    def _call_blocking(self, tool_name: str, arguments: dict) -> str:
        if self.client is None or not self.client.alive:
            self._reconnect()
        assert self.client is not None
        try:
            res = self.client.request("tools/call", {"name": tool_name, "arguments": arguments})
        except ServerGone as exc:
            log.warning("mcp %s gone during %s: %s", self.name, tool_name, exc)
            self.close()
            raise TransientToolError(f"mcp server {self.name} disconnected") from exc
        except RuntimeError as exc:  # JSON-RPC error: the server rejected the call
            raise ValueError(str(exc)) from exc
        text = " ".join(c["text"] for c in res.get("content", []) if c.get("type") == "text")
        if res.get("isError"):
            from aiapp.runtime.errors import ToolFailed

            raise ToolFailed(text or f"{tool_name} reported an error")
        return text

    def _reconnect(self) -> None:
        try:
            self.connect()
            log.info("mcp %s reconnected", self.name)
        except (OSError, ServerGone, RuntimeError) as exc:
            self.client = None
            raise TransientToolError(f"mcp server {self.name} unavailable: {exc}") from exc
