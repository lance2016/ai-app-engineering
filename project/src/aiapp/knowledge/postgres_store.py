"""PostgreSQL KnowledgeStore: pgvector for the vector path, tsvector for the text path, one database for both."""

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from aiapp.adapters.embeddings import tokenize
from aiapp.knowledge.base import Chunk, Document, Hit, IngestReport
from aiapp.storage.models import ChunkRow, DocumentRow

HIT_COLUMNS = (ChunkRow.chunk_id, ChunkRow.doc_id, ChunkRow.version, ChunkRow.section, ChunkRow.start, ChunkRow.end, ChunkRow.text)


class PostgresKnowledgeStore:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    @classmethod
    def from_url(cls, url: str) -> "PostgresKnowledgeStore":
        return cls(create_async_engine(url, pool_pre_ping=True))

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def existing_hashes(self, tenant_id: str, doc_id: str) -> set[str]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(select(ChunkRow.content_hash).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc_id))
        return {h for (h,) in rows}

    async def upsert_document(self, tenant_id: str, doc: Document, chunks: list[Chunk], vectors: list[list[float] | None], embedding_model: str) -> IngestReport:
        async with self._engine.begin() as conn:
            old = await conn.execute(select(ChunkRow.content_hash, ChunkRow.embedding).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc.doc_id))
            by_hash = {h: list(v) if v is not None else None for h, v in old}
            await conn.execute(delete(ChunkRow).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc.doc_id))
            embedded = reused = 0
            for chunk, vector in zip(chunks, vectors):
                if vector is None:
                    vector = by_hash[chunk.content_hash]
                    reused += 1
                else:
                    embedded += 1
                await conn.execute(
                    ChunkRow.__table__.insert().values(
                        tenant_id=tenant_id, chunk_id=chunk.chunk_id, doc_id=chunk.doc_id, version=chunk.version, section=chunk.section,
                        start=chunk.start, end=chunk.end, text=chunk.text, content_hash=chunk.content_hash,
                        embedding=vector, embedding_model=embedding_model,
                    )
                )
            await conn.execute(delete(DocumentRow).where(DocumentRow.tenant_id == tenant_id, DocumentRow.doc_id == doc.doc_id))
            await conn.execute(DocumentRow.__table__.insert().values(tenant_id=tenant_id, doc_id=doc.doc_id, version=doc.version, title=doc.title))
        removed = len(set(by_hash) - {c.content_hash for c in chunks})
        return IngestReport(doc.doc_id, doc.version, len(chunks), embedded, reused, removed)

    async def search_vector(self, tenant_id: str, query_vector: list[float], *, k: int, embedding_model: str) -> list[Hit]:
        distance = ChunkRow.embedding.cosine_distance(query_vector)
        stmt = (
            select(*HIT_COLUMNS, distance.label("distance"))
            .where(ChunkRow.tenant_id == tenant_id, ChunkRow.embedding_model == embedding_model, ChunkRow.embedding.is_not(None))
            .order_by(distance)
            .limit(k)
        )
        async with self._engine.connect() as conn:
            rows = await conn.execute(stmt)
        return [_hit(r, 1.0 - float(r.distance), "vector") for r in rows]

    async def search_text(self, tenant_id: str, query: str, *, k: int) -> list[Hit]:
        """OR over the query terms, like BM25: a chunk matching some words still ranks. plainto_tsquery would AND them and miss."""
        terms = tokenize(query)
        if not terms:
            return []
        tsq = func.to_tsquery("simple", " | ".join(dict.fromkeys(terms)))
        rank = func.ts_rank(ChunkRow.tsv, tsq)
        stmt = select(*HIT_COLUMNS, rank.label("rank")).where(ChunkRow.tenant_id == tenant_id, ChunkRow.tsv.op("@@")(tsq)).order_by(rank.desc()).limit(k)
        async with self._engine.connect() as conn:
            rows = await conn.execute(stmt)
        return [_hit(r, float(r.rank), "text") for r in rows]

    async def delete_document(self, tenant_id: str, doc_id: str) -> int:
        async with self._engine.begin() as conn:
            result = await conn.execute(delete(ChunkRow).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc_id))
            await conn.execute(delete(DocumentRow).where(DocumentRow.tenant_id == tenant_id, DocumentRow.doc_id == doc_id))
        return result.rowcount or 0

    async def list_documents(self, tenant_id: str) -> list[tuple[str, int, str]]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(select(DocumentRow.doc_id, DocumentRow.version, DocumentRow.title).where(DocumentRow.tenant_id == tenant_id).order_by(DocumentRow.doc_id))
        return [tuple(r) for r in rows]

    async def residue(self, tenant_id: str, doc_id: str) -> dict[str, int]:
        async with self._engine.connect() as conn:
            chunks = await conn.scalar(select(func.count()).select_from(ChunkRow).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc_id))
            docs = await conn.scalar(select(func.count()).select_from(DocumentRow).where(DocumentRow.tenant_id == tenant_id, DocumentRow.doc_id == doc_id))
            vectors = await conn.scalar(select(func.count()).select_from(ChunkRow).where(ChunkRow.tenant_id == tenant_id, ChunkRow.doc_id == doc_id, ChunkRow.embedding.is_not(None)))
        return {"chunks": int(chunks or 0), "documents": int(docs or 0), "embeddings": int(vectors or 0)}


def _hit(r, score: float, source: str) -> Hit:
    return Hit(r.chunk_id, r.doc_id, r.version, r.section, r.start, r.end, r.text, round(score, 6), source)


__all__ = ["PostgresKnowledgeStore", "text"]
