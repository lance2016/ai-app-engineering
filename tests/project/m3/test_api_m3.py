"""The HTTP surface of M3: tool events over SSE, the human-input endpoint, request-level allowlists."""

from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse, tool_call_response
from aiapp.api import create_app
from aiapp.tools.demo import DocStore, build_default_registry
from tests.project.m1.conftest import AUTH_A, make_settings, parse_sse


def app_with(script, **settings) -> tuple[TestClient, DocStore]:
    registry, docs = build_default_registry()
    model = FakeAdapter(script=script, chunk_size=8)
    client = TestClient(create_app(settings=make_settings(**settings), model=model, registry=registry), raise_server_exceptions=False)
    return client, docs


def post_sse(client: TestClient, path: str, body: dict) -> tuple[int, list]:
    r = client.post(path, json=body, headers=AUTH_A)
    raw = r.read().decode()
    if r.headers.get("content-type", "").startswith("text/event-stream"):
        return r.status_code, parse_sse(raw)
    import json

    return r.status_code, json.loads(raw) if raw else {}


def test_tool_calls_stream_as_events(monkeypatch) -> None:
    client, _ = app_with([tool_call_response("search_docs", {"query": "shipping"}, call_id="c1"), ModelResponse(content="Free over 50.")])
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    status, frames = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "shipping cost?"})
    assert status == 200
    kinds = [t for t, _ in frames if t != "assistant_delta"]
    assert kinds == ["user_message", "run_started", "assistant_message", "tool_result", "assistant_message", "run_finished"]
    tool_result = dict(frames)["tool_result"]
    assert tool_result["name"] == "search_docs" and tool_result["route"] == "ok" and "doc_shipping" in tool_result["content"]
    assert set(dict(frames)["run_started"]["allowlist"]) == {"search_docs", "read_doc", "delete_doc", "load_skill", "read_skill_reference", "search_knowledge"}


def test_confirmation_round_trip_over_http() -> None:
    client, docs = app_with([tool_call_response("delete_doc", {"doc_id": "doc_returns_draft", "reason": "draft"}, call_id="c1"), ModelResponse(content="Gone.")])
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    status, frames = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "delete the draft"})
    assert status == 200 and frames[-1][0] == "human_input_requested" and frames[-1][1]["kind"] == "confirmation"
    assert docs.deleted == []
    assert client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()["status"] == "paused"

    status, body = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "hurry up"})
    assert status == 409, "while paused, new messages are rejected: answer first"

    status, body = post_sse(client, f"/v1/threads/{tid}/human-input", {"confirm_tool_call_id": "wrong", "approved": True})
    assert status == 422 and body["code"] == "invalid_request"

    status, frames = post_sse(client, f"/v1/threads/{tid}/human-input", {"confirm_tool_call_id": "c1", "approved": True})
    assert status == 200
    assert [t for t, _ in frames if t != "assistant_delta"] == ["human_input", "run_started", "tool_result", "assistant_message", "run_finished"]
    assert docs.deleted == ["doc_returns_draft"]
    assert client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()["status"] == "finished"

    status, body = post_sse(client, f"/v1/threads/{tid}/human-input", {"confirm_tool_call_id": "c1", "approved": True})
    assert status == 409, "nothing is waiting any more"


def test_question_round_trip_over_http() -> None:
    client, _ = app_with([tool_call_response("request_human_input", {"question": "Which one?"}, call_id="q1"), ModelResponse(content="Refunds it is.")])
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    _, frames = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "tell me about the policy"})
    assert frames[-1][1] == {"tool_call_id": "q1", "kind": "question", "question": "Which one?"}
    status, frames = post_sse(client, f"/v1/threads/{tid}/human-input", {"tool_call_id": "q1", "content": "refunds"})
    assert status == 200 and frames[-1][0] == "run_finished" and frames[-1][1]["answer"] == "Refunds it is."


def test_request_can_narrow_but_not_widen_the_allowlist() -> None:
    client, docs = app_with([tool_call_response("delete_doc", {"doc_id": "doc_refunds"}, call_id="c1"), ModelResponse(content="Cannot.")], tool_allowlist=frozenset({"search_docs", "read_doc"}))
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    status, frames = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "delete", "allowed_tools": ["search_docs", "read_doc", "delete_doc"]})
    assert status == 200
    assert dict(frames)["tool_result"]["route"] == "not_allowed", "asking for delete_doc does not grant it"
    assert docs.deleted == []
    status, body = post_sse(client, f"/v1/threads/{tid}/messages", {"content": "x", "allowed_tools": ["no_such_tool"]})
    assert status == 422 and "unknown tools" in body["message"]
