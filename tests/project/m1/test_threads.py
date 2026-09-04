from fastapi.testclient import TestClient

from aiapp.prompts import load_prompt
from tests.project.m1.conftest import AUTH_A, AUTH_B, make_client, parse_sse


def test_create_and_read_thread(client: TestClient) -> None:
    created = client.post("/v1/threads", json={"title": "laptops"}, headers=AUTH_A)
    assert created.status_code == 201
    body = created.json()
    assert body["tenant_id"] == "tenant-a"
    assert body["status"] == "running"  # it has one event (thread_created) and no run yet
    assert [e["type"] for e in body["events"]] == ["thread_created"]

    read = client.get(f"/v1/threads/{body['thread_id']}", headers=AUTH_A)
    assert read.status_code == 200
    assert read.json() == body


def test_threads_are_invisible_to_other_tenants(client: TestClient, thread_id: str) -> None:
    r = client.get(f"/v1/threads/{thread_id}", headers=AUTH_B)
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"


def test_send_message_streams_lesson_07_events_then_persists_them(client: TestClient, thread_id: str) -> None:
    with client.stream("POST", f"/v1/threads/{thread_id}/messages", json={"content": "hello"}, headers=AUTH_A) as r:
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/event-stream")
        assert r.headers["X-Prompt-Version"] == "v1"
        frames = parse_sse(r.read().decode())

    types = [t for t, _ in frames]
    assert types[:2] == ["user_message", "run_started"]
    assert types[-2:] == ["assistant_message", "run_finished"]
    deltas = "".join(d["content"] for t, d in frames if t == "assistant_delta")
    assert deltas == "Hello from the fake model."
    assert dict(frames)["assistant_message"]["content"] == deltas
    assert dict(frames)["run_finished"]["usage"]["output_tokens"] > 0

    stored = client.get(f"/v1/threads/{thread_id}", headers=AUTH_A).json()
    assert stored["status"] == "finished"
    assert [e["type"] for e in stored["events"]] == ["user_message", "run_started", "assistant_message", "run_finished"]
    assert all(e["type"] != "assistant_delta" for e in stored["events"]), "deltas are streamed, never stored"


def test_model_sees_versioned_system_prompt_then_history(client: TestClient, thread_id: str) -> None:
    client.post(f"/v1/threads/{thread_id}/messages", json={"content": "first"}, headers=AUTH_A).read()
    client.post(f"/v1/threads/{thread_id}/messages", json={"content": "second"}, headers=AUTH_A).read()
    calls = client.model.calls  # type: ignore[attr-defined]
    assert calls[0][0].role == "system" and calls[0][0].content.startswith(load_prompt("assistant", "v1"))  # M3 appends the skill catalog
    assert [m.role for m in calls[1]] == ["system", "user", "assistant", "user"]
    assert calls[1][-1].content == "second"


def test_switching_prompt_version_changes_header_and_prompt() -> None:
    client = make_client(prompt_version="v2")
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": "hi"}, headers=AUTH_A)
    r.read()
    assert r.headers["X-Prompt-Version"] == "v2"
    assert client.model.calls[0][0].content.startswith(load_prompt("assistant", "v2"))  # type: ignore[attr-defined]
    assert load_prompt("assistant", "v1") != load_prompt("assistant", "v2")
