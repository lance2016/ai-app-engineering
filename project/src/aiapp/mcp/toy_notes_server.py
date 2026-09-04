"""A toy MCP notes server: JSON-RPC 2.0 over stdio, one JSON object per line.

Implements initialize, notifications/initialized, ping, tools/list, tools/call,
resources/list, resources/read. Tools carry the spec's ``annotations.readOnlyHint``
so a client can tell which ones change the world.

Usage (normally launched by the client):
    python -m aiapp.mcp.toy_notes_server [--read-only] [--crash-on METHOD] [--crash-once]
"""

import json
import sys

PROTOCOL_VERSION = "2026-07-28"
NOTES = {"notes://todo": "buy milk\ncall mum", "notes://ideas": "write an MCP lesson", "notes://policy": "refunds within 30 days"}

TOOLS = {
    "search_notes": {
        "description": "Search the user's notes. Read-only.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "annotations": {"readOnlyHint": True},
    },
    "delete_note": {
        "description": "Delete a note by uri. Irreversible.",
        "inputSchema": {"type": "object", "properties": {"uri": {"type": "string"}}, "required": ["uri"]},
        "annotations": {"readOnlyHint": False, "destructiveHint": True},
    },
}


def error(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def result(req_id, payload: dict) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": payload}


def call_tool(name: str, args: dict) -> dict:
    """Tool failures are results with isError, not JSON-RPC errors (spec: tools/call)."""
    if name == "search_notes":
        hits = [uri for uri, text in NOTES.items() if args["query"].lower() in text.lower()]
        return {"content": [{"type": "text", "text": json.dumps(hits)}], "isError": False}
    if name == "delete_note":
        if args["uri"] not in NOTES:
            return {"content": [{"type": "text", "text": f"no such note {args['uri']}"}], "isError": True}
        del NOTES[args["uri"]]
        return {"content": [{"type": "text", "text": f"deleted {args['uri']}"}], "isError": False}
    raise KeyError(name)


def handle(msg: dict, *, read_only: bool, initialized: bool) -> tuple[dict | None, bool]:
    method, req_id, params = msg.get("method"), msg.get("id"), msg.get("params") or {}
    if method == "initialize":
        caps = {"tools": {"listChanged": False}, "resources": {"subscribe": False, "listChanged": False}}
        return result(req_id, {"protocolVersion": PROTOCOL_VERSION, "capabilities": caps, "serverInfo": {"name": "toy-notes", "version": "0.2.0"}}), initialized
    if method == "notifications/initialized":
        return None, True
    if not initialized:
        return error(req_id, -32600, "server not initialized"), initialized
    if method == "ping":
        return result(req_id, {}), initialized
    visible = {n: t for n, t in TOOLS.items() if not (read_only and not t["annotations"].get("readOnlyHint"))}
    if method == "tools/list":
        return result(req_id, {"tools": [{"name": n, **t} for n, t in visible.items()]}), initialized
    if method == "tools/call":
        name = params.get("name")
        if name not in visible:
            return error(req_id, -32602, f"unknown tool: {name}"), initialized
        args = params.get("arguments") or {}
        missing = [k for k in TOOLS[name]["inputSchema"]["required"] if k not in args]
        if missing:
            return error(req_id, -32602, f"invalid params: missing {missing}"), initialized
        return result(req_id, call_tool(name, args)), initialized
    if method == "resources/list":
        return result(req_id, {"resources": [{"uri": u, "name": u.split("//")[1], "mimeType": "text/plain"} for u in NOTES]}), initialized
    if method == "resources/read":
        uri = params.get("uri")
        if uri not in NOTES:
            return error(req_id, -32002, f"resource not found: {uri}"), initialized
        return result(req_id, {"contents": [{"uri": uri, "mimeType": "text/plain", "text": NOTES[uri]}]}), initialized
    return error(req_id, -32601, f"method not found: {method}"), initialized


def main() -> None:
    read_only = "--read-only" in sys.argv
    crash_on = sys.argv[sys.argv.index("--crash-on") + 1] if "--crash-on" in sys.argv else None
    initialized = False
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if crash_on and msg.get("method") == crash_on:
            sys.exit(1)  # simulate the server process dying mid-request
        reply, initialized = handle(msg, read_only=read_only, initialized=initialized)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
