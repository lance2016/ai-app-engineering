import pytest
from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse
from aiapp.adapters.inject import FailingAdapter, SlowAdapter, apply_injection
from aiapp.config import Settings, parse_tokens
from tests.project.m1.conftest import AUTH_A, StallingAdapter, make_client, parse_sse

ENVELOPE_KEYS = {"code", "message", "request_id"}


def test_missing_and_invalid_tokens_are_401_with_the_envelope(client: TestClient) -> None:
    missing = client.post("/v1/threads", json={})
    invalid = client.post("/v1/threads", json={}, headers={"Authorization": "Bearer nope"})
    for r in (missing, invalid):
        assert r.status_code == 401
        assert set(r.json()) == ENVELOPE_KEYS
        assert r.json()["code"] == "unauthorized"
        assert r.json()["request_id"] == r.headers["X-Request-ID"]


def test_bad_body_is_422_with_the_same_envelope(client: TestClient, thread_id: str) -> None:
    empty = client.post(f"/v1/threads/{thread_id}/messages", json={"content": ""}, headers=AUTH_A)
    wrong_field = client.post(f"/v1/threads/{thread_id}/messages", json={"text": "hi"}, headers=AUTH_A)
    not_json = client.post(f"/v1/threads/{thread_id}/messages", content=b"{not json", headers={**AUTH_A, "Content-Type": "application/json"})
    for r in (empty, wrong_field, not_json):
        assert r.status_code == 422, r.text
        assert set(r.json()) == ENVELOPE_KEYS
        assert r.json()["code"] == "invalid_request"
    assert "content" in empty.json()["message"]


def test_unknown_thread_is_404(client: TestClient) -> None:
    r = client.post("/v1/threads/thr_missing/messages", json={"content": "hi"}, headers=AUTH_A)
    assert r.status_code == 404
    assert r.json()["code"] == "not_found"


def test_slow_model_becomes_504_before_any_bytes_are_streamed() -> None:
    """Failure injection: the model takes 10s, the timeout is 0.3s. The client gets a real status code."""
    client = make_client(model=SlowAdapter(FakeAdapter(), delay_s=10), model_timeout_s=0.3)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": "hi"}, headers=AUTH_A)
    assert r.status_code == 504
    assert r.json()["code"] == "model_timeout"
    stored = client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()
    assert stored["status"] == "failed"
    assert stored["events"][-1]["data"].items() >= {"reason": "model_timeout", "stage": "first_chunk"}.items()


def test_provider_outage_becomes_502() -> None:
    client = make_client(model=FailingAdapter(FakeAdapter()))
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": "hi"}, headers=AUTH_A)
    assert r.status_code == 502
    assert r.json()["code"] == "provider_error"
    assert "503" not in r.json()["message"], "provider details stay in the log, not in the client-facing message"


def test_stall_after_first_chunk_ends_the_stream_with_run_failed() -> None:
    client = make_client(model=StallingAdapter(), model_timeout_s=0.2)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    with client.stream("POST", f"/v1/threads/{tid}/messages", json={"content": "hi"}, headers=AUTH_A) as r:
        assert r.status_code == 200  # bytes were already flowing; the failure is reported in-band
        frames = parse_sse(r.read().decode())
    assert [t for t, _ in frames] == ["user_message", "run_started", "assistant_delta", "run_failed"]
    assert frames[-1][1]["stage"] == "mid_stream" and frames[-1][1]["partial"] == "Once upon"
    assert client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()["status"] == "failed"


def test_injection_switch_wraps_the_adapter() -> None:
    assert apply_injection(FakeAdapter(), None).name == "fake"
    assert apply_injection(FakeAdapter(), "slow_model").name == "slow(fake)"
    assert apply_injection(FakeAdapter(), "provider_error").name == "failing(fake)"
    with pytest.raises(ValueError):
        apply_injection(FakeAdapter(), "typo")


def test_settings_parse_tokens_and_reject_garbage() -> None:
    assert parse_tokens("a:tenant-1, b:tenant-2") == {"a": "tenant-1", "b": "tenant-2"}
    assert parse_tokens(None) == {} and parse_tokens("") == {}
    with pytest.raises(ValueError):
        parse_tokens("no-colon")
    s = Settings.from_env({"AIAPP_TOKENS": "x:t", "AIAPP_MODEL_TIMEOUT_S": "2.5", "AIAPP_INJECT": ""})
    assert s.tokens == {"x": "t"} and s.model_timeout_s == 2.5 and s.inject is None


def test_unknown_prompt_version_fails_at_startup() -> None:
    with pytest.raises(FileNotFoundError):
        make_client(prompt_version="v99")
