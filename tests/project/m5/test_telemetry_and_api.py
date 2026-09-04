"""Spans with GenAI attributes for a run; readiness; 429 / 402 through HTTP; structured logs carry the trace id."""

import json
import logging
from decimal import Decimal

from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse, tool_call_response
from aiapp.adapters.inject import FailingAdapter
from aiapp.api import create_app
from aiapp.config import Settings
from aiapp.ops import telemetry
from aiapp.ops.logging import JsonFormatter, log_event
from aiapp.runtime import ToolRegistry
from aiapp.tools.demo import DocStore
from tests.project.m1.conftest import AUTH_A, make_settings


def client_with(script, registry=None, **settings) -> TestClient:
    model = FakeAdapter(script=script, chunk_size=10)
    return TestClient(create_app(settings=make_settings(**settings), model=model, registry=registry), raise_server_exceptions=False)


def spans_by_name() -> dict[str, list]:
    telemetry.flush()
    out: dict[str, list] = {}
    for s in telemetry.recorded_spans():
        out.setdefault(s.name.split(" ")[0], []).append(s)
    return out


def test_a_run_produces_the_genai_span_tree() -> None:
    docs = DocStore(fail_next_searches=10)
    registry = ToolRegistry()
    docs.register_into(registry)
    client = client_with([tool_call_response("search_docs", {"query": "refund"}, call_id="c1"), ModelResponse(content="Backend down.")], registry=registry)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    telemetry.clear_recorded_spans()
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": "refund policy?"}, headers={**AUTH_A, "X-Request-ID": "req-otel"})
    r.read()
    spans = spans_by_name()
    assert set(spans) >= {"POST", "invoke_agent", "chat", "execute_tool", "cost.charge"}
    assert spans["chat"][0].parent.span_id == spans["invoke_agent"][0].context.span_id
    assert spans["execute_tool"][0].parent.span_id == spans["invoke_agent"][0].context.span_id
    http = spans["POST"][0]
    assert http.attributes["aiapp.request_id"] == "req-otel" and http.attributes["aiapp.prompt_version"] == "v1"
    root = spans["invoke_agent"][0]
    assert root.attributes["gen_ai.operation.name"] == "invoke_agent" and root.attributes["aiapp.tenant_id"] == "tenant-a" and root.attributes["aiapp.stop_reason"] == "finished"
    assert root.parent is not None and root.parent.span_id == http.context.span_id, "the agent run hangs under the HTTP span"
    chat = spans["chat"]
    assert len(chat) == 2 and all(c.attributes["gen_ai.usage.input_tokens"] > 0 for c in chat) and chat[0].attributes["gen_ai.response.finish_reasons"] == ("tool_calls",)
    tool = spans["execute_tool"][0]
    assert tool.attributes["gen_ai.tool.name"] == "search_docs" and tool.attributes["aiapp.tool.route"] == "transient_exhausted" and tool.attributes["aiapp.tool.attempts"] == 3
    assert tool.status.status_code.name == "ERROR", "an error result marks the span ERROR, not just an event"
    charge = spans_by_name()["cost.charge"][0]
    assert charge.attributes["aiapp.cost_usd"] > 0 and charge.parent.span_id == http.context.span_id


def test_model_timeout_marks_chat_and_root_spans_error() -> None:
    from aiapp.adapters.inject import SlowAdapter

    client = TestClient(create_app(settings=make_settings(model_timeout_s=0.05), model=SlowAdapter(FakeAdapter(), delay_s=5)), raise_server_exceptions=False)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    telemetry.clear_recorded_spans()
    assert client.post(f"/v1/threads/{tid}/messages", json={"content": "hi"}, headers=AUTH_A).status_code == 504
    spans = spans_by_name()
    assert spans["chat"][0].status.status_code.name == "ERROR" and spans["chat"][0].attributes["error.type"] == "TimeoutError"
    assert spans["invoke_agent"][0].status.status_code.name == "ERROR" and spans["invoke_agent"][0].attributes["aiapp.stop_reason"] == "model_timeout"


def test_rate_limit_returns_429_with_retry_after_and_isolates_tenants() -> None:
    client = client_with([ModelResponse(content="ok")] * 10, rate_limit_rps=0.01, rate_limit_burst=1)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    first = client.post(f"/v1/threads/{tid}/messages", json={"content": "a"}, headers=AUTH_A)
    first.read()
    second = client.post(f"/v1/threads/{tid}/messages", json={"content": "b"}, headers=AUTH_A)
    assert first.status_code == 200 and second.status_code == 429
    assert second.json()["code"] == "rate_limited" and int(second.headers["Retry-After"]) >= 1
    other = client.post("/v1/threads", json={}, headers={"Authorization": "Bearer token-b"}).json()["thread_id"]
    assert client.post(f"/v1/threads/{other}/messages", json={"content": "a"}, headers={"Authorization": "Bearer token-b"}).status_code == 200


def test_budget_returns_402_and_ledger_records_usage() -> None:
    client = client_with([ModelResponse(content="x" * 200)] * 5, daily_budget_usd=0.00001)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    ok = client.post(f"/v1/threads/{tid}/messages", json={"content": "hello"}, headers=AUTH_A)
    ok.read()
    blocked = client.post(f"/v1/threads/{tid}/messages", json={"content": "again"}, headers=AUTH_A)
    assert ok.status_code == 200 and blocked.status_code == 402 and blocked.json()["code"] == "budget_exhausted"
    import anyio

    ledger = client.app.state.cost_ledger
    spent = anyio.run(ledger.store.spent_today, "tenant-a", ledger.today())
    assert spent > Decimal(0)


def test_readiness_reports_each_dependency() -> None:
    healthy = client_with([ModelResponse(content="ok")])
    r = healthy.get("/readyz")
    assert r.status_code == 200 and r.json()["ready"] is True and set(r.json()["checks"]) == {"model"}
    down = TestClient(create_app(settings=make_settings(), model=FailingAdapter(FakeAdapter())), raise_server_exceptions=False)
    r = down.get("/readyz")
    assert r.status_code == 503 and r.json()["checks"]["model"]["ok"] is False
    unreachable = TestClient(create_app(settings=make_settings(redis_url="redis://127.0.0.1:1/0"), model=FakeAdapter()), raise_server_exceptions=False)
    r = unreachable.get("/readyz")
    assert r.status_code == 503 and r.json()["checks"]["redis"]["ok"] is False and "postgres" not in r.json()["checks"]


def test_production_mode_refuses_unsafe_configuration() -> None:
    import pytest

    with pytest.raises(RuntimeError, match="refusing to start in production"):
        create_app(settings=Settings(env="production"), model=FakeAdapter())
    problems = Settings(env="production", tokens={"real": "tenant"}, database_url="postgresql+asyncpg://x", redis_url="redis://x", inject="slow_model").validate_for_production()
    assert problems == ["AIAPP_INJECT='slow_model' is a failure injection"]


def test_json_logs_carry_fields_and_trace_id() -> None:
    import io

    stream = io.StringIO()
    logger = logging.getLogger("aiapp.test.json")
    logger.handlers.clear()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    with telemetry.span("unit test"):
        log_event(logger, "tool.call", tool="search_docs", latency_ms=12.5)
    line = json.loads(stream.getvalue().strip())
    assert line["event"] == "tool.call" and line["tool"] == "search_docs" and line["latency_ms"] == 12.5
    assert len(line["trace_id"]) == 32
