"""Every KnowledgeStore passes these, on memory and PostgreSQL + pgvector."""

import pytest

from aiapp.adapters.embeddings import HashingEmbedding
from aiapp.knowledge import Retriever, parse_markdown
from tests.project.m4.conftest import GOLDEN, load_docs, tenant

pytestmark = pytest.mark.anyio


class CountingEmbedder(HashingEmbedding):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def embed(self, texts):
        self.calls += len(texts)
        return await super().embed(texts)


async def test_ingest_then_hybrid_search_finds_the_answer_with_provenance(retriever: Retriever) -> None:
    t = tenant()
    for doc in load_docs():
        report = await retriever.ingest(t, doc)
        assert report.embedded == report.chunks and report.reused == 0 and report.problems == []
    hits = await retriever.search("same day dispatch cutoff", tenant_id=t, k=3)
    assert hits and hits[0].doc_id == "shipping" and "14:00 cutoff" in hits[0].text
    assert hits[0].citation_id == f"shipping@v1#{hits[0].chunk_id.split('#')[1]}" and hits[0].source == "hybrid"


async def test_tenants_never_see_each_other(retriever: Retriever) -> None:
    a, b = tenant(), tenant()
    await retriever.ingest(a, parse_markdown("secret", "# Secret\n\nthe launch codes are 1234"))
    await retriever.ingest(b, parse_markdown("public", "# Public\n\nshipping is free over 50"))
    assert [h.doc_id for h in await retriever.search("launch codes", tenant_id=b, k=5)] == ["public"] or not await retriever.search("launch codes", tenant_id=b, k=5)
    assert all(h.doc_id == "secret" for h in await retriever.search("launch codes", tenant_id=a, k=5))
    assert await retriever.store.list_documents(b) == [("public", 1, "Public")]


async def test_new_version_replaces_old_chunks_and_reuses_unchanged_vectors(knowledge_store) -> None:
    embedder = CountingEmbedder()
    retriever = Retriever(knowledge_store, embedder)
    t = tenant()
    v1 = "# Policy\n\nRefunds within 30 days.\n\n# Contact\n\nEmail support."
    v2 = "# Policy\n\nRefunds within 14 days.\n\n# Contact\n\nEmail support."
    r1 = await retriever.ingest(t, parse_markdown("policy", v1, version=1))
    calls_after_v1 = embedder.calls
    r2 = await retriever.ingest(t, parse_markdown("policy", v2, version=2))
    assert (r1.embedded, r1.reused) == (2, 0)
    assert (r2.embedded, r2.reused, r2.removed) == (1, 1, 1), "only the changed section was re-embedded"
    assert embedder.calls - calls_after_v1 == 1
    hits = await retriever.search("refund days", tenant_id=t, k=5)
    assert hits and all(h.version == 2 for h in hits)
    assert not any("30 days" in h.text for h in hits), "the old version is gone from retrieval"
    assert any("14 days" in h.text for h in hits)
    assert await knowledge_store.list_documents(t) == [("policy", 2, "Policy")]


async def test_delete_leaves_no_residue_anywhere(retriever: Retriever) -> None:
    t = tenant()
    for doc in load_docs():
        await retriever.ingest(t, doc)
    removed = await retriever.store.delete_document(t, "warranty")
    assert removed > 0
    assert all(v == 0 for v in (await retriever.store.residue(t, "warranty")).values())
    assert not any(h.doc_id == "warranty" for h in await retriever.search("liquid damage warranty", tenant_id=t, k=10))
    assert (await retriever.store.residue(t, "shipping"))["chunks"] > 0, "other documents untouched"
    assert await retriever.store.delete_document(t, "warranty") == 0


async def test_vectors_from_another_model_are_never_compared(knowledge_store) -> None:
    t = tenant()
    a, b = Retriever(knowledge_store, HashingEmbedding(dim=256)), Retriever(knowledge_store, HashingEmbedding(dim=64))
    await a.ingest(t, parse_markdown("d1", "# One\n\nshipping is free over fifty"))
    await b.ingest(t, parse_markdown("d2", "# Two\n\nshipping costs six under fifty"))
    q = (await a.embedder.embed(["shipping"]))[0]
    vector_hits = await knowledge_store.search_vector(t, q, k=10, embedding_model=a.embedder.name)
    assert [h.doc_id for h in vector_hits] == ["d1"], "d2 was embedded by a different model and must not appear in this space"
    assert {h.doc_id for h in await knowledge_store.search_text(t, "shipping", k=10)} == {"d1", "d2"}, "the text path does not care"


async def test_recall_at_5_on_the_golden_set_meets_the_baseline(retriever: Retriever) -> None:
    """Baseline recorded in the M4 README: hybrid Recall@5 = 0.90 with the hashing embedding (2026-09-04)."""
    t = tenant()
    for doc in load_docs():
        await retriever.ingest(t, doc)
    hits_at_5 = 0
    for g in GOLDEN:
        ranked = await retriever.search(g["q"], tenant_id=t, k=5)
        hits_at_5 += any(g["must_contain"] in h.text for h in ranked)
    recall = hits_at_5 / len(GOLDEN)
    assert recall >= 0.85, f"hybrid Recall@5 fell to {recall:.2f}"
