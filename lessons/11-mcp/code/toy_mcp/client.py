"""Minimal MCP-shaped client: spawns a server subprocess and speaks JSON-RPC over its stdio."""

import json
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).with_name("server.py")


class ServerGone(Exception):
    """The server closed its stdout: it crashed or exited."""


class ToyMcpClient:
    def __init__(self, *server_args: str, timeout: float = 5.0):
        self._proc = subprocess.Popen(
            [sys.executable, str(SERVER), *server_args],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
        )
        self._next_id = 0
        self._timeout = timeout
        self.server_info: dict = {}
        self.capabilities: dict = {}

    # ---- transport ------------------------------------------------------------
    def _send(self, msg: dict) -> None:
        try:
            self._proc.stdin.write(json.dumps(msg) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, ValueError) as exc:
            raise ServerGone("stdin closed") from exc

    def request(self, method: str, params: dict | None = None) -> dict:
        """Send a request, block for its response. Raises ServerGone on EOF, RuntimeError on JSON-RPC error."""
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": self._next_id, "method": method, "params": params or {}})
        line = self._proc.stdout.readline()
        if not line:
            raise ServerGone(f"no response to {method}; exit code {self._proc.poll()}")
        reply = json.loads(line)
        if "error" in reply:
            raise RuntimeError(f"{reply['error']['code']}: {reply['error']['message']}")
        return reply["result"]

    def notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    # ---- lifecycle --------------------------------------------------------------
    def initialize(self) -> dict:
        info = self.request("initialize", {
            "protocolVersion": "2026-07-28",
            "capabilities": {},
            "clientInfo": {"name": "lesson-11-client", "version": "0.1.0"},
        })
        self.server_info, self.capabilities = info["serverInfo"], info["capabilities"]
        self.notify("notifications/initialized")
        return info

    def close(self) -> None:
        if self._proc.poll() is None:
            self._proc.stdin.close()
            try:
                self._proc.wait(timeout=self._timeout)
            except subprocess.TimeoutExpired:
                self._proc.kill()
                self._proc.wait()

    def __enter__(self) -> "ToyMcpClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
