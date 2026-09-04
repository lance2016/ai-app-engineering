"""Documents in, cited answers out, citations verified; memories extracted, recalled into the next turn, forgotten."""

import json

from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse, tool_call_response
from aiapp.api import create_app
from tests.project.m1.conftest import AUTH_A, make_settings, parse_sse
from tests.project.m4.conftest import DOCS

USER = {**AUTH_A, "X-User-ID": "u42"}


def app_with(script) -> TestClient:
    model = FakeAdapter(script=script, chunk_size=10)
    client = TestClient(create_app(settings=make_settings(), model=model), raise_server_exceptions=False)
    client.model = model  # type: ignore[attr-defined]
    return client


def ingest_all(client: TestClient) -> None:
    for path in sorted(DOCS.glob("*.md")):
        r = client.post("/v1/documents", json={"doc_id": path.stem, "text": path.read_text(encoding="utf-8")}, headers=AUTH_A)
        assert r.status_code == 201 and r.json()["chunks"] > 0


def run_turn(client: TestClient, tid: str, content: str, headers=AUTH_A) -> list:
    r = client.post(f"/v1/threads/{tid}/messages", json={"content": content}, headers=headers)
    assert r.status_code == 200, r.text
    return parse_sse(r.read().decode())


def test_answer_with_verified_citations() -> None:
    client = app_with([tool_call_response("search_knowledge", {"query": "same day dispatch cutoff"}, call_id="k1"), ModelResponse(content="PLACEHOLDER")])
    ingest_all(client)
    assert len(client.get("/v1/documents", headers=AUTH_A).json()) == 6
    search = client.get("/v1/knowledge/search", params={"q": "dispatch cutoff"}, headers=AUTH_A).json()
    cid = next(s["citation_id"] for s in search if "14:00 cutoff" in s["text"])
    client.model._script[-1] = ModelResponse(content=f"Orders placed before the 14:00 cutoff are dispatched the same day [{cid}].")  # type: ignore[attr-defined]

    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    frames = run_turn(client, tid, "When is the same day dispatch cutoff?")
    kinds = [t for t, _ in frames if t != "assistant_delta"]
    assert kinds[-2:] == ["run_finished", "citations_checked"]
    check = dict(frames)["citations_checked"]
    assert check["ok"] is True and check["cited"] == [cid]
    tool_result = dict(frames)["tool_result"]
    assert tool_result["name"] == "search_knowledge" and cid in tool_result["content"]
    system = client.model.calls[0][0].content  # type: ignore[attr-defined]
    assert "cite the source" in system, "citation instructions are added when the knowledge tool is available"


def test_made_up_citation_is_caught() -> None:
    client = app_with([tool_call_response("search_knowledge", {"query": "refund"}, call_id="k1"), ModelResponse(content="Refunds take 24 hours [shipping@v1#99].")])
    ingest_all(client)
    tid = client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
    check = dict(run_turn(client, tid, "how fast are refunds?"))["citations_checked"]
    assert check["ok"] is False and any("never retrieved" in p for p in check["problems"])
    stored = client.get(f"/v1/threads/{tid}", headers=AUTH_A).json()
    assert stored["events"][-1]["type"] == "citations_checked", "the verdict is part of the thread, so evaluation can read it later"


def test_delete_document_proves_zero_residue_and_search_forgets_it() -> None:
    client = app_with([ModelResponse(content="x")])
    ingest_all(client)
    r = client.delete("/v1/documents/warranty", headers=AUTH_A)
    assert r.status_code == 200 and r.json()["removed_chunks"] > 0 and all(v == 0 for v in r.json()["residue"].values())
    assert not any(s["doc_id"] == "warranty" for s in client.get("/v1/knowledge/search", params={"q": "liquid damage warranty", "k": 10}, headers=AUTH_A).json())
    assert client.delete("/v1/documents/warranty", headers=AUTH_A).status_code == 404
    assert client.get("/v1/documents", headers={"Authorization": "Bearer token-b"}).json() == [], "other tenant sees nothing"


def test_memories_are_extracted_recalled_next_turn_and_forgotten() -> None:
    extraction = json.dumps({"memories": [
        {"content": "cannot eat spicy food", "kind": "preference", "subject": "spice", "source_event_seqs": [0]},
        {"content": "has a vegetarian daughter", "kind": "fact", "subject": "family", "source_event_seqs": [0]},
    ]})
    client = app_with([ModelResponse(content="Noted."), ModelResponse(content=extraction), ModelResponse(content="How about a mild Thai place with vegetarian mains?"), ModelResponse(content="Sure.")])
    tid = client.post("/v1/threads", json={}, headers=USER).json()["thread_id"]
    run_turn(client, tid, "Nothing spicy for me, and my daughter is vegetarian.", headers=USER)

    r = client.post(f"/v1/threads/{tid}/memories", headers=USER)
    assert r.status_code == 201 and [o["outcome"] for o in r.json()["outcomes"]] == ["added", "added"]
    memories = client.get("/v1/memories", headers=USER).json()
    assert sorted(m["content"] for m in memories) == ["cannot eat spicy food", "has a vegetarian daughter"]
    assert client.get("/v1/memories", headers=AUTH_A).json() == [], "no X-User-ID means a different user (the tenant itself)"

    tid2 = client.post("/v1/threads", json={}, headers=USER).json()["thread_id"]
    run_turn(client, tid2, "Recommend a restaurant for my daughter and me", headers=USER)
    window = client.model.calls[2]  # type: ignore[attr-defined]
    assert window[1].role == "user" and "vegetarian daughter" in window[1].content and "spicy" in window[1].content

    r = client.delete("/v1/memories", params={"subject": "family"}, headers=USER)
    assert r.status_code == 200 and len(r.json()["forgotten"]) == 1 and "source_event_seqs" in r.json()["audit"]
    tid3 = client.post("/v1/threads", json={}, headers=USER).json()["thread_id"]
    run_turn(client, tid3, "Recommend a restaurant for my daughter", headers=USER)
    window = client.model.calls[3]  # type: ignore[attr-defined]
    assert "daughter" not in window[1].content and "spicy" in window[1].content, "forgotten memories never reach the model again"
    history = client.get("/v1/memories", params={"include_history": "true"}, headers=USER).json()
    assert any(m["active"] is False and m["deleted_reason"] for m in history)


def test_extraction_without_provenance_is_a_422() -> None:
    client = app_with([ModelResponse(content="ok"), ModelResponse(content=json.dumps({"memories": [{"content": "likes tea", "kind": "preference", "subject": "drink", "source_event_seqs": []}]}))])
    tid = client.post("/v1/threads", json={}, headers=USER).json()["thread_id"]
    run_turn(client, tid, "I like tea", headers=USER)
    r = client.post(f"/v1/threads/{tid}/memories", headers=USER)
    assert r.status_code == 422 and r.json()["code"] == "invalid_request"
    assert client.get("/v1/memories", headers=USER).json() == []
