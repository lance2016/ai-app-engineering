"""Ingest and retrieve: embed what changed, search both ways, fuse, return hits with provenance."""

from dataclasses import dataclass

from aiapp.adapters.embeddings import EmbeddingAdapter
from aiapp.knowledge.base import Document, Hit, IngestReport, KnowledgeStore
from aiapp.knowledge.hybrid import rrf
from aiapp.knowledge.ingest import chunk_document, quality_problems


@dataclass
class Retriever:
    store: KnowledgeStore
    embedder: EmbeddingAdapter
    max_chars: int = 600

    async def ingest(self, tenant_id: str, doc: Document) -> IngestReport:
        chunks = chunk_document(doc, max_chars=self.max_chars)
        problems = quality_problems(chunks)
        known = await self.store.existing_hashes(tenant_id, doc.doc_id)
        todo = [i for i, c in enumerate(chunks) if c.content_hash not in known]
        fresh = await self.embedder.embed([chunks[i].text for i in todo]) if todo else []
        vectors: list[list[float] | None] = [None] * len(chunks)
        for i, vec in zip(todo, fresh):
            vectors[i] = vec
        report = await self.store.upsert_document(tenant_id, doc, chunks, vectors, self.embedder.name)
        report.problems = problems
        return report

    async def search(self, query: str, *, tenant_id: str, k: int = 8, candidates: int = 20) -> list[Hit]:
        """Vector and text rankings fused with RRF. Tenant is a hard filter on every path."""
        qvec = (await self.embedder.embed([query]))[0]
        by_vector = await self.store.search_vector(tenant_id, qvec, k=candidates, embedding_model=self.embedder.name)
        by_text = await self.store.search_text(tenant_id, query, k=candidates)
        return rrf(by_vector, by_text, limit=k)
