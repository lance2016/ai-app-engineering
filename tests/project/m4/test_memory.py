"""Memory: provenance required, consolidation per subject, per-user recall, provable forgetting."""

import json

import pytest

from aiapp import FakeAdapter, ModelResponse, Thread
from aiapp.adapters.embeddings import HashingEmbedding
from aiapp.knowledge.memory import ExtractionRejected, MemoryService, extract_candidates
from tests.project.m4.conftest import tenant

pytestmark = pytest.mark.anyio


def conversation() -> Thread:
    t = Thread()
    t.append("user_message", content="Can you recommend a restaurant for Friday?")
    t.append("assistant_message", content="Sure. Any preferences?", tool_calls=[])
    t.append("user_message", content="Nothing spicy, I can't handle it. And my daughter is vegetarian.")
    t.append("assistant_message", content="Got it.", tool_calls=[])
    return t


def extractor(memories: list[dict]) -> FakeAdapter:
    return FakeAdapter(script=[ModelResponse(content=json.dumps({"memories": memories}))])


SPICE = {"content": "cannot eat spicy food", "kind": "preference", "subject": "spice", "source_event_seqs": [2]}
DAUGHTER = {"content": "has a vegetarian daughter", "kind": "fact", "subject": "family", "source_event_seqs": [2]}


async def test_extraction_without_provenance_is_rejected() -> None:
    with pytest.raises(ExtractionRejected):
        await extract_candidates(conversation(), extractor([{**SPICE, "source_event_seqs": []}]))
    with pytest.raises(ExtractionRejected, match="not user messages"):
        await extract_candidates(conversation(), extractor([{**SPICE, "source_event_seqs": [1]}]))  # points at the assistant
    with pytest.raises(ExtractionRejected):
        await extract_candidates(conversation(), FakeAdapter(script=[ModelResponse(content="not json at all")]))


async def test_remember_adds_dedupes_and_supersedes_per_subject(memory_store) -> None:
    svc = MemoryService(memory_store, HashingEmbedding())
    t, user = tenant(), "u42"
    first = await svc.remember(t, user, conversation(), extractor([SPICE, DAUGHTER]))
    assert [o for o, _ in first] == ["added", "added"]
    second = await svc.remember(t, user, conversation(), extractor([SPICE, {"content": "started eating spicy food again", "kind": "preference", "subject": "spice", "source_event_seqs": [2]}]))
    outcomes = [o for o, _ in second]
    assert outcomes[0] == "duplicate" and outcomes[1].startswith("superseded ")
    active = await memory_store.active_for(t, user)
    assert sorted(m.content for m in active) == ["has a vegetarian daughter", "started eating spicy food again"]
    history = await memory_store.history(t, user)
    assert len(history) == 3 and any(m.superseded_by for m in history), "the old statement is kept as history, never shown"


async def test_recall_is_per_user_and_relevance_ranked(memory_store) -> None:
    svc = MemoryService(memory_store, HashingEmbedding())
    t = tenant()
    await svc.remember(t, "u42", conversation(), extractor([SPICE, DAUGHTER, {"content": "prefers morning meetings", "kind": "preference", "subject": "schedule", "source_event_seqs": [0]}]))
    await svc.remember(t, "u99", conversation(), extractor([{"content": "is allergic to peanuts", "kind": "fact", "subject": "allergy", "source_event_seqs": [2]}]))
    hits = await svc.recall(t, "u42", "recommend a restaurant with spicy food for my daughter", k=3)
    contents = [m.content for m in hits]
    assert "cannot eat spicy food" in contents and "has a vegetarian daughter" in contents
    assert "is allergic to peanuts" not in contents, "another user's memory leaked"
    assert all(m.user_id == "u42" for m in hits)


async def test_forget_is_targeted_and_leaves_an_audit_trail(memory_store) -> None:
    svc = MemoryService(memory_store, HashingEmbedding())
    t, user = tenant(), "u42"
    await svc.remember(t, user, conversation(), extractor([SPICE, DAUGHTER]))
    removed = await svc.forget(t, user, subject="family", reason="user said: forget what I told you about my daughter")
    assert [m.content for m in removed] == ["has a vegetarian daughter"] and removed[0].deleted_reason.startswith("user said")
    assert [m.content for m in await memory_store.active_for(t, user)] == ["cannot eat spicy food"]
    assert not any("daughter" in m.content for m in await svc.recall(t, user, "restaurant for my daughter"))
    audit = [m for m in await memory_store.history(t, user) if not m.active]
    assert len(audit) == 1 and audit[0].source_event_seqs == (2,), "the deletion can be proven later: what, why, where it came from"
