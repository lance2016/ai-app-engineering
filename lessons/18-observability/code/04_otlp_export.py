"""Ship the hand-rolled spans to a real backend: OTLP/HTTP JSON, no SDK required.

Phoenix, Langfuse and every OpenTelemetry collector accept the same JSON
shape on /v1/traces. Building it by hand once demystifies what the SDK does
and proves the attribute names are the only contract that matters.

Run:  uv run python lessons/18-observability/code/04_otlp_export.py                           # prints the payload
      OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:6006 uv run python lessons/18-observability/code/04_otlp_export.py   # posts to Phoenix
Expect: an OTLP JSON document; with an endpoint set, an HTTP status from the collector.
"""

# %% imports
import json
import os
import time
import urllib.error
import urllib.request
import uuid

ENDPOINT = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")


# %% build_spans
def make_span(trace_id: str, name: str, parent: str | None, attrs: dict, status_code: int, start: float, end: float) -> dict:
    return {
        "traceId": trace_id,
        "spanId": uuid.uuid4().hex[:16],
        **({"parentSpanId": parent} if parent else {}),
        "name": name,
        "kind": 1,  # SPAN_KIND_INTERNAL
        "startTimeUnixNano": str(int(start * 1e9)),
        "endTimeUnixNano": str(int(end * 1e9)),
        "attributes": [{"key": k, "value": otlp_value(v)} for k, v in attrs.items()],
        "status": {"code": status_code},  # 0 UNSET, 1 OK, 2 ERROR
    }


def otlp_value(v) -> dict:
    if isinstance(v, bool):
        return {"boolValue": v}
    if isinstance(v, int):
        return {"intValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": str(v)}


def build_payload() -> dict:
    trace_id = uuid.uuid4().hex
    now = time.time()
    root = make_span(trace_id, "invoke_agent support_bot", None, {"gen_ai.operation.name": "invoke_agent", "gen_ai.agent.name": "support_bot"}, 1, now - 1.2, now)
    chat = make_span(trace_id, "chat deepseek-chat", root["spanId"], {"gen_ai.operation.name": "chat", "gen_ai.provider.name": "deepseek", "gen_ai.request.model": "deepseek-chat", "gen_ai.usage.input_tokens": 182, "gen_ai.usage.output_tokens": 24}, 1, now - 1.1, now - 0.6)
    tool = make_span(trace_id, "execute_tool search", root["spanId"], {"gen_ai.operation.name": "execute_tool", "gen_ai.tool.name": "search", "error.type": "TimeoutError"}, 2, now - 0.6, now - 0.1)
    return {"resourceSpans": [{
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "aiapp-lesson18"}}]},
        "scopeSpans": [{"scope": {"name": "aiapp.minimal_tracer", "version": "0.0.1"}, "spans": [root, chat, tool]}],
    }]}


# %% export
def export(payload: dict) -> None:
    body = json.dumps(payload).encode()
    if not ENDPOINT:
        print(json.dumps(payload, indent=2)[:1800] + "\n... (set OTEL_EXPORTER_OTLP_ENDPOINT to actually send this)")
        return
    req = urllib.request.Request(f"{ENDPOINT.rstrip('/')}/v1/traces", data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"exported 3 spans -> {resp.status} {resp.reason}; open {ENDPOINT} and look for service aiapp-lesson18")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"export failed: {exc}. Is the collector running? Phoenix: `pip install arize-phoenix && phoenix serve` then port 6006.")


if __name__ == "__main__":
    export(build_payload())
