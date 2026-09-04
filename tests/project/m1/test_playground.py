from fastapi.testclient import TestClient


def test_playground_page_is_served_without_auth(client: TestClient) -> None:
    r = client.get("/playground")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "/v1/threads" in r.text  # the page talks to the real API, it is not a mock


def test_playground_does_not_leak_into_the_api_schema(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert "/playground" not in paths
