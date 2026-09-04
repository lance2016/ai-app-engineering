"""Minimal MCP client: spawn a server subprocess and speak JSON-RPC over its stdio."""

import json
import subprocess
from dataclasses import dataclass, field

PROTOCOL_VERSION = "2026-07-28"


class ServerGone(Exception):
    """The server closed its stdout: it crashed or exited."""


@dataclass
class StdioMcpClient:
    command: list[str]
    timeout_s: float = 5.0
    server_info: dict = field(default_factory=dict, init=False)
    capabilities: dict = field(default_factory=dict, init=False)
    _proc: subprocess.Popen | None = field(default=None, init=False, repr=False)
    _next_id: int = field(default=0, init=False, repr=False)

    def connect(self) -> dict:
        """Spawn the process and run the lifecycle: initialize -> initialized."""
        self._proc = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        info = self.request("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": {"name": "aiapp", "version": "0.3.0"}})
        self.server_info, self.capabilities = info["serverInfo"], info["capabilities"]
        self.notify("notifications/initialized")
        return info

    @property
    def alive(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _send(self, msg: dict) -> None:
        if self._proc is None or self._proc.stdin is None:
            raise ServerGone("not connected")
        try:
            self._proc.stdin.write(json.dumps(msg) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, ValueError, OSError) as exc:
            raise ServerGone("stdin closed") from exc

    def request(self, method: str, params: dict | None = None) -> dict:
        """Raises ServerGone on EOF, RuntimeError on a JSON-RPC error."""
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}})
        assert self._proc is not None and self._proc.stdout is not None
        line = self._proc.stdout.readline()
        if not line:
            raise ServerGone(f"no response to {method}; exit code {self._proc.poll()}")
        reply = json.loads(line)
        if "error" in reply:
            raise RuntimeError(f"{reply['error']['code']}: {reply['error']['message']}")
        return reply["result"]

    def notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def close(self) -> None:
        if self._proc is None:
            return
        if self._proc.poll() is None:
            if self._proc.stdin:
                self._proc.stdin.close()
            try:
                self._proc.wait(timeout=self.timeout_s)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()
        self._proc = None
