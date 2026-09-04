"""In-memory KnowledgeStore: brute-force cosine plus BM25. The contract tests run on it and on PostgreSQL."""

import math
from collections import Counter
from dataclasses import dataclass, field

from aiapp.adapters.embeddings import cosine, tokenize
from aiapp.knowledge.base import Chunk, Document, Hit, IngestReport


@dataclass
class _Row:
    tenant_id: str
    chunk: Chunk
    vector: list[float] | None
    embedding_model: str | None


@dataclass
class InMemoryKnowledgeStore:
    rows: dict[tuple[str, str], _Row] = field(default_factory=dict)  # (tenant, chunk_id) -> row
    documents: dict[tuple[str, str], tuple[int, str]] = field(default_factory=dict)  # (tenant, doc_id) -> (version, title)
    answer_cache: dict[tuple[str, str], str] = field(default_factory=dict)  # (tenant, doc_id) -> anything derived, for the residue drill

    def _doc_rows(self, tenant_id: str, doc_id: str) -> dict[tuple[str, str], _Row]:
        return {k: r for k, r in self.rows.items() if k[0] == tenant_id and r.chunk.doc_id == doc_id}

    async def existing_hashes(self, tenant_id: str, doc_id: str) -> set[str]:
        return {r.chunk.content_hash for r in self._doc_rows(tenant_id, doc_id).values()}

    async def upsert_document(self, tenant_id: str, doc: Document, chunks: list[Chunk], vectors: list[list[float] | None], embedding_model: str) -> IngestReport:
        old = self._doc_rows(tenant_id, doc_id=doc.doc_id)
        by_hash = {r.chunk.content_hash: r for r in old.values()}
        for key in old:
            del self.rows[key]
        embedded = reused = 0
        for chunk, vector in zip(chunks, vectors):
            if vector is None:
                vector = by_hash[chunk.content_hash].vector
                reused += 1
            else:
                embedded += 1
            self.rows[(tenant_id, chunk.chunk_id)] = _Row(tenant_id, chunk, vector, embedding_model)
        removed = len(set(by_hash) - {c.content_hash for c in chunks})
        self.documents[(tenant_id, doc.doc_id)] = (doc.version, doc.title)
        return IngestReport(doc.doc_id, doc.version, len(chunks), embedded, reused, removed)

    async def search_vector(self, tenant_id: str, query_vector: list[float], *, k: int, embedding_model: str) -> list[Hit]:
        scored = [
            (cosine(query_vector, r.vector), r.chunk)
            for (t, _), r in self.rows.items()
            if t == tenant_id and r.vector is not None and r.embedding_model == embedding_model
        ]
        scored.sort(key=lambda x: -x[0])
        return [_hit(c, s, "vector") for s, c in scored[:k]]

    async def search_text(self, tenant_id: str, query: str, *, k: int) -> list[Hit]:
        chunks = [r.chunk for (t, _), r in self.rows.items() if t == tenant_id]
        if not chunks:
            return []
        bm25 = _BM25(chunks)
        scored = sorted(((bm25.score(query, i), c) for i, c in enumerate(chunks)), key=lambda x: -x[0])
        return [_hit(c, s, "text") for s, c in scored[:k] if s > 0]

    async def delete_document(self, tenant_id: str, doc_id: str) -> int:
        rows = self._doc_rows(tenant_id, doc_id)
        for key in rows:
            del self.rows[key]
        self.documents.pop((tenant_id, doc_id), None)
        self.answer_cache.pop((tenant_id, doc_id), None)
        return len(rows)

    async def list_documents(self, tenant_id: str) -> list[tuple[str, int, str]]:
        return sorted((d, v, t) for (tenant, d), (v, t) in self.documents.items() if tenant == tenant_id)

    async def residue(self, tenant_id: str, doc_id: str) -> dict[str, int]:
        return {
            "chunks": len(self._doc_rows(tenant_id, doc_id)),
            "documents": int((tenant_id, doc_id) in self.documents),
            "answer_cache": int((tenant_id, doc_id) in self.answer_cache),
        }


def _hit(c: Chunk, score: float, source: str) -> Hit:
    return Hit(c.chunk_id, c.doc_id, c.version, c.section, c.start, c.end, c.text, round(float(score), 6), source)


class _BM25:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: str, i: int) -> float:
        d, dl = self.docs[i], self.lengths[i]
        s = 0.0
        for t in tokenize(query):
            if t in d:
                tf = d[t]
                s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
        return s
