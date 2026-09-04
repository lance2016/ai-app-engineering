"""Chaos drills: inject one failure into an in-process app, drive a request, check the system did what it should, show the trace.

Run:  uv run python scripts/chaos.py --inject model_timeout
      uv run python scripts/chaos.py --inject provider_down       # primary dead -> fallback serves, breaker opens
      uv run python scripts/chaos.py --inject tool_error
      uv run python scripts/chaos.py --inject empty_retrieval
      uv run python scripts/chaos.py --inject budget
      uv run python scripts/chaos.py --inject rate_limit
      uv run python scripts/chaos.py --all
Every scenario prints PASS/FAIL against its expected behaviour and the spans that show where it failed.
Exit 1 if any scenario's expectation is not met.
"""

import argparse
import sys
from dataclasses import dataclass, field
from decimal import Decimal

from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse, tool_call_response
from aiapp.adapters.inject import FailingAdapter, SlowAdapter
from aiapp.api import create_app
from aiapp.config import Settings
from aiapp.ops import telemetry
from aiapp.ops.cost import CostLedger
from aiapp.ops.resilience import CircuitBreaker, FallbackAdapter
from aiapp.runtime import ToolRegistry
from aiapp.tools.demo import DocStore

AUTH = {"Authorization": "Bearer chaos-token", "Content-Type": "application/json"}


@dataclass
class Scenario:
    name: str
    expect: str
    ok: bool = False
    observed: str = ""
    spans: list[str] = field(default_factory=list)


def make_client(model, **settings) -> TestClient:
    registry, docs = None, None
    if "registry" in settings:
        registry = settings.pop("registry")
    app = create_app(settings=Settings(tokens={"chaos-token": "tenant-chaos"}, model_timeout_s=0.3, **settings), model=model, registry=registry)
    return TestClient(app, raise_server_exceptions=False)


def new_thread(client: TestClient) -> str:
    return client.post("/v1/threads", json={}, headers=AUTH).json()["thread_id"]


def send(client: TestClient, tid: str, text: str, allowed=None):
    body = {"content": text} | ({"allowed_tools": allowed} if allowed else {})
    r = client.post(f"/v1/threads/{tid}/messages", json=body, headers=AUTH)
    return r.status_code, r.read().decode(), dict(r.headers)


def frames(body: str) -> list[tuple[str, dict]]:
    import json

    out = []
    for block in body.strip().split("\n\n"):
        event, data = None, {}
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        if event:
            out.append((event, data))
    return out


def span_lines() -> list[str]:
    telemetry.flush()
    out = []
    for s in telemetry.recorded_spans():
        status = s.status.status_code.name
        attrs = {k: v for k, v in s.attributes.items() if k.startswith(("gen_ai.", "aiapp.", "error."))}
        out.append(f"{s.name:32} [{status:5}] {attrs}")
    return out


def scenario_model_timeout() -> Scenario:
    sc = Scenario("model_timeout", "504 model_timeout before any bytes; chat span ERROR TimeoutError; thread status failed")
    client = make_client(SlowAdapter(FakeAdapter(), delay_s=5))
    tid = new_thread(client)
    telemetry.clear_recorded_spans()
    status, body, _ = send(client, tid, "hello")
    stored = client.get(f"/v1/threads/{tid}", headers=AUTH).json()
    sc.spans = span_lines()
    sc.observed = f"HTTP {status}, thread status {stored['status']}"
    sc.ok = status == 504 and stored["status"] == "failed" and any("chat" in l and "ERROR" in l for l in sc.spans)
    return sc


def scenario_provider_down() -> Scenario:
    sc = Scenario("provider_down", "request succeeds via fallback; breaker opens after 3 failures; later requests skip the primary")
    primary = FailingAdapter(FakeAdapter(), "provider is down")
    secondary = FakeAdapter(script=[ModelResponse(content="fallback answer")] * 10)
    secondary.name = "fallback-fake"
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_s=60)
    model = FallbackAdapter(primary, secondary, breaker, primary_timeout_s=0.3)
    client = make_client(model)
    telemetry.clear_recorded_spans()
    statuses = []
    for _ in range(4):
        tid = new_thread(client)
        status, body, _ = send(client, tid, "hello")
        statuses.append(status)
    sc.spans = span_lines()
    sc.observed = f"HTTP {statuses}, breaker={breaker.state}, served_by={model.served_by}, primary attempts stopped once open"
    sc.ok = all(s == 200 for s in statuses) and breaker.state.value == "open" and model.served_by["fallback"] == 4
    return sc


def scenario_tool_error() -> Scenario:
    sc = Scenario("tool_error", "transient tool failures retried then reported as an error result; execute_tool span ERROR; run finishes")
    docs = DocStore(fail_next_searches=10)
    registry = ToolRegistry()
    docs.register_into(registry)
    model = FakeAdapter(script=[tool_call_response("search_docs", {"query": "refund"}), ModelResponse(content="The search backend is unavailable right now.")])
    client = make_client(model, registry=registry)
    tid = new_thread(client)
    telemetry.clear_recorded_spans()
    status, body, _ = send(client, tid, "refund policy?")
    sc.spans = span_lines()
    sc.observed = f"HTTP {status}, tool_result route=transient_exhausted in stream: {'transient_exhausted' in body}"
    sc.ok = status == 200 and "transient_exhausted" in body and "run_finished" in body and any("execute_tool" in l and "ERROR" in l for l in sc.spans)
    return sc


def scenario_empty_retrieval() -> Scenario:
    sc = Scenario("empty_retrieval", "no documents indexed: search_knowledge returns zero sources, the model says so, citations_checked is skipped")
    model = FakeAdapter(script=[tool_call_response("search_knowledge", {"query": "refund"}), ModelResponse(content="I could not find anything about that in the knowledge base.")])
    client = make_client(model)
    tid = new_thread(client)
    telemetry.clear_recorded_spans()
    status, body, _ = send(client, tid, "refund policy?")
    sc.spans = span_lines()
    import json

    kinds = dict(frames(body))
    sources = json.loads(kinds.get("tool_result", {}).get("content", "{}")).get("sources")
    sc.observed = f"HTTP {status}, sources={sources}, citations_checked present: {'citations_checked' in kinds}, finished: {'run_finished' in kinds}"
    sc.ok = status == 200 and sources == [] and "citations_checked" not in kinds and "run_finished" in kinds
    return sc


def scenario_budget() -> Scenario:
    sc = Scenario("budget", "first request charged; once the daily budget is spent the next request is 402 budget_exhausted")
    client = make_client(FakeAdapter(script=[ModelResponse(content="x" * 400)] * 5), daily_budget_usd=0.00001)
    tid = new_thread(client)
    telemetry.clear_recorded_spans()
    first, _, _ = send(client, tid, "hello")
    second, body, _ = send(client, tid, "hello again")
    ledger: CostLedger = client.app.state.cost_ledger
    import asyncio

    spent = asyncio.run(ledger.store.spent_today("tenant-chaos", ledger.today()))
    sc.spans = span_lines()
    sc.observed = f"first HTTP {first}, second HTTP {second} ({'budget_exhausted' in body}), spent {spent} USD"
    sc.ok = first == 200 and second == 402 and spent > Decimal(0)
    return sc


def scenario_rate_limit() -> Scenario:
    sc = Scenario("rate_limit", "burst of 4 with capacity 2 at 0.1 rps: two 200s then 429 with Retry-After; another tenant unaffected")
    client = make_client(FakeAdapter(), rate_limit_rps=0.1, rate_limit_burst=2)
    client.app.state.settings = Settings(tokens={"chaos-token": "tenant-chaos", "other": "tenant-other"}, model_timeout_s=0.3, rate_limit_rps=0.1, rate_limit_burst=2)
    tid = new_thread(client)
    telemetry.clear_recorded_spans()
    statuses, retry_after = [], None
    for _ in range(4):
        status, _, headers = send(client, tid, "hi")
        statuses.append(status)
        retry_after = retry_after or headers.get("retry-after")
    other = client.post("/v1/threads", json={}, headers={"Authorization": "Bearer other", "Content-Type": "application/json"}).json()["thread_id"]
    other_status = client.post(f"/v1/threads/{other}/messages", json={"content": "hi"}, headers={"Authorization": "Bearer other", "Content-Type": "application/json"}).status_code
    sc.spans = span_lines()
    sc.observed = f"HTTP {statuses}, Retry-After={retry_after}, other tenant HTTP {other_status}"
    sc.ok = statuses[:2] == [200, 200] and statuses[2:] == [429, 429] and retry_after is not None and other_status == 200
    return sc


SCENARIOS = {
    "model_timeout": scenario_model_timeout,
    "provider_down": scenario_provider_down,
    "tool_error": scenario_tool_error,
    "empty_retrieval": scenario_empty_retrieval,
    "budget": scenario_budget,
    "rate_limit": scenario_rate_limit,
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inject", choices=sorted(SCENARIOS))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--spans", action="store_true", help="print every span, not only the interesting ones")
    args = parser.parse_args()
    names = sorted(SCENARIOS) if args.all or not args.inject else [args.inject]
    telemetry.setup_tracing(in_memory=True)
    failed = 0
    for name in names:
        sc = SCENARIOS[name]()
        failed += not sc.ok
        print(f"\n== {sc.name}: {'PASS' if sc.ok else 'FAIL'}")
        print(f"   expected: {sc.expect}")
        print(f"   observed: {sc.observed}")
        interesting = [l for l in sc.spans if args.spans or "ERROR" in l or "invoke_agent" in l]
        for line in interesting[:12]:
            print(f"   span: {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
