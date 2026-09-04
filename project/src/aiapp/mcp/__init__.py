"""A small MCP client over stdio, plus a toy notes server used by tests and the M3 demo.

Not the official SDK: the course keeps the wire protocol visible (JSON-RPC 2.0,
newline-delimited). Swapping in the official client later touches only
``MCPToolSource``.
"""

from aiapp.mcp.client import ServerGone, StdioMcpClient

__all__ = ["ServerGone", "StdioMcpClient"]
