"""The HTTP surface on top of M2 storage: durable checkpoints, the run lock, idempotent replays."""

import json

import pytest
from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse
from aiapp.api import create_app
from aiapp.storage.memory import InMemoryKeyValueStore, InMemoryThreadStore
from tests.project.m1.conftest import AUTH_A, make_settings, parse_sse


@pytest.fixture(params=["memory", "real"])
def backend(request):
    """(store_factory, kv_factory): memory pairs, or PostgreSQL + Redis when reachable."""
    if request.param == "memory":
        store, kv = InMemoryThreadStore(), InMemoryKeyValueStore()
        return (lambda: store), (lambda: kv)
    from aiapp.storage.postgres import PostgresThreadStore
    from aiapp.storage.redis_kv import RedisKeyValueStore

    pg, rd = request.getfixturevalue("postgres_url"), request.getfixturevalue("redis_url")
    return (lambda: PostgresThreadStore.from_url(pg)), (lambda: RedisKeyValueStore.from_url(rd))


def app_client(backend, model=None) -> TestClient:
    store_factory, kv_factory = backend
    model = model or FakeAdapter(script=[ModelResponse(content="Answer one."), ModelResponse(content="Answer two.")], chunk_size=5)
    client = TestClient(create_app(settings=make_settings(), model=model, store=store_factory(), kv=kv_factory()), raise_server_exceptions=False)
    client.model = model  # type: ignore[attr-defined]
    return client


def kv_do(kv_factory, method: str, *args) -> object:
    """Touch the key-value store from the test, on its own client and loop (a Redis client is bound to one loop)."""
    import anyio

    async def go():
        kv = kv_factory()
        try:
            return await getattr(kv, method)(*args)
        finally:
            if hasattr(kv, "close"):
                await kv.close()

    return anyio.run(go)


def send(client: TestClient, tid: str, content: str, **headers) -> tuple[int, dict, list]:
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": content}, headers={**AUTH_A, **headers})
    body = r.read().decode()
    frames = parse_sse(body) if r.headers.get("content-type", "").startswith("text/event-stream") else []
    return r.status_code, dict(r.headers), frames if frames else (json.loads(body) if body else {})


def test_history_survives_a_process_restart(backend) -> None:
    with app_client(backend) as first:
        tid = first.post("/v1/threads", json={"title": "durable"}, headers=AUTH_A).json()["thread_id"]
        status, _, frames = send(first, tid, "hello")
        assert status == 200 and frames[-1][0] == "run_finished"

    with app_client(backend) as second:  # new app, new store object, same storage
        stored = second.get(f"/v1/threads/{tid}", headers=AUTH_A).json()
    assert stored["status"] == "finished"
    assert [e["type"] for e in stored["events"]] == ["thread_created", "user_message", "run_started", "assistant_message", "run_finished"]
    assert stored["events"][-1]["data"]["answer"] == "Answer one."


def test_second_message_during_a_run_is_rejected(backend) -> None:
    """Double texting, reject strategy: the lock is held for the whole run. Here we hold it by hand."""
    store_factory, kv_factory = backend
    with app_client(backend) as client:
        tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
        assert kv_do(kv_factory, "claim", f"run:{tid}", "another-worker", 30) is True
        status, _, body = send(client, tid, "second message")
        assert status == 409 and body["code"] == "conflict"
        assert "in progress" in body["message"]
        assert kv_do(kv_factory, "release", f"run:{tid}", "another-worker") is True
        status, _, frames = send(client, tid, "now it works")
        assert status == 200 and frames[-1][0] == "run_finished"
        assert len(client.model.calls) == 1, "the rejected message never reached the model"  # type: ignore[attr-defined]


def test_lock_is_released_after_the_run_so_the_next_turn_works(backend) -> None:
    with app_client(backend) as client:
        tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
        assert send(client, tid, "one")[0] == 200
        assert send(client, tid, "two")[0] == 200
        assert len(client.model.calls) == 2  # type: ignore[attr-defined]


def test_same_idempotency_key_replays_without_a_second_model_call(backend) -> None:
    with app_client(backend) as client:
        tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
        status1, headers1, frames1 = send(client, tid, "charge my card", **{"Idempotency-Key": "req-42"})
        status2, headers2, frames2 = send(client, tid, "charge my card", **{"Idempotency-Key": "req-42"})
        assert status1 == status2 == 200
        assert "x-idempotent-replay" not in {k.lower() for k in headers1}
        assert headers2.get("x-idempotent-replay") == "true"

        persisted_types = [t for t, _ in frames1 if t != "assistant_delta"]
        assert [t for t, _ in frames2] == persisted_types, "the replay is exactly the first run's persisted events"
        assert dict(frames2)["assistant_message"] == dict(frames1)["assistant_message"]
        assert len(client.model.calls) == 1, "one side effect, however many retries"  # type: ignore[attr-defined]

        stored = client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()
        assert [e["type"] for e in stored["events"]].count("user_message") == 1


def test_idempotency_key_still_in_flight_is_a_conflict(backend) -> None:
    store_factory, kv_factory = backend
    with app_client(backend) as client:
        tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
        kv_do(kv_factory, "claim", f"idem:tenant-a:{tid}:req-7", "claimed", 30)
        status, _, body = send(client, tid, "again", **{"Idempotency-Key": "req-7"})
        assert status == 409 and body["code"] == "conflict"


def test_failed_run_releases_the_lock_and_records_nothing_for_the_key(backend) -> None:
    from aiapp.adapters.inject import FailingAdapter

    with app_client(backend, model=FailingAdapter(FakeAdapter())) as client:
        tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
        status, _, body = send(client, tid, "hi", **{"Idempotency-Key": "k1"})
        assert status == 502
        status, _, body = send(client, tid, "hi", **{"Idempotency-Key": "k1"})
        assert status == 502, "a failed attempt is not replayed; the retry really retries"
        stored = client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()
        assert [e["type"] for e in stored["events"]] == ["user_message", "run_started", "run_failed"] * 2
