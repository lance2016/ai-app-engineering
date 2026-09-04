from fastapi.testclient import TestClient


def test_healthz_reports_model_and_prompt_version(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "model": "fake", "prompt_version": "v1"}


def test_every_response_carries_a_request_id(client: TestClient) -> None:
    generated = client.get("/healthz").headers["X-Request-ID"]
    echoed = client.get("/healthz", headers={"X-Request-ID": "req-123"}).headers["X-Request-ID"]
    assert len(generated) == 12
    assert echoed == "req-123"
