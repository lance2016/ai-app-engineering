"""PostgreSQL MemoryStore over the ``memory`` table. Soft deletes keep the audit trail."""

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from aiapp.adapters.embeddings import tokenize
from aiapp.knowledge.memory import Memory
from aiapp.storage.models import MemoryRow


MEMORY_COLUMNS = (
    MemoryRow.id, MemoryRow.tenant_id, MemoryRow.user_id, MemoryRow.content, MemoryRow.kind, MemoryRow.subject, MemoryRow.source_thread_id,
    MemoryRow.source_event_seqs, MemoryRow.created_at, MemoryRow.superseded_by, MemoryRow.active, MemoryRow.deleted_reason,
)


def _to_memory(r) -> Memory:
    return Memory(r.id, r.tenant_id, r.user_id, r.content, r.kind, r.subject, r.source_thread_id, tuple(r.source_event_seqs), r.created_at, r.superseded_by, r.active, r.deleted_reason)


class PostgresMemoryStore:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    @classmethod
    def from_url(cls, url: str) -> "PostgresMemoryStore":
        return cls(create_async_engine(url, pool_pre_ping=True))

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def add(self, memory: Memory, vector, embedding_model) -> Memory:
        async with self._engine.begin() as conn:
            await conn.execute(MemoryRow.__table__.insert().values(
                id=memory.id, tenant_id=memory.tenant_id, user_id=memory.user_id, content=memory.content, kind=memory.kind, subject=memory.subject,
                source_thread_id=memory.source_thread_id, source_event_seqs=list(memory.source_event_seqs), embedding=vector, embedding_model=embedding_model,
                created_at=memory.created_at, active=True,
            ))
        return memory

    async def active_for(self, tenant_id: str, user_id: str) -> list[Memory]:
        stmt = select(*MEMORY_COLUMNS).where(MemoryRow.tenant_id == tenant_id, MemoryRow.user_id == user_id, MemoryRow.active.is_(True), MemoryRow.superseded_by.is_(None)).order_by(MemoryRow.created_at)
        async with self._engine.connect() as conn:
            return [_to_memory(r) for r in await conn.execute(stmt)]

    async def search(self, tenant_id: str, user_id: str, query_vector, query: str, *, k: int, embedding_model) -> list[Memory]:
        """Vector distance when both sides have a vector of the same model, plus a keyword bonus; tenant and user are hard filters."""
        active = await self.active_for(tenant_id, user_id)
        if len(active) <= k:
            return active  # few memories: show them all; the ranking matters once there are many
        scores: dict[str, float] = {m.id: 0.0 for m in active}
        if query_vector is not None and embedding_model:
            stmt = (
                select(MemoryRow.id, MemoryRow.embedding.cosine_distance(query_vector))
                .where(MemoryRow.tenant_id == tenant_id, MemoryRow.user_id == user_id, MemoryRow.active.is_(True), MemoryRow.superseded_by.is_(None), MemoryRow.embedding_model == embedding_model)
            )
            async with self._engine.connect() as conn:
                for mid, dist in await conn.execute(stmt):
                    scores[mid] += 1.0 - float(dist)
        words = set(tokenize(query))
        for m in active:
            scores[m.id] += 0.5 * len(words & set(tokenize(m.content + " " + m.subject)))
        ranked = sorted((m for m in active if scores[m.id] > 0), key=lambda m: -scores[m.id])
        return ranked[:k]

    async def supersede(self, old_id: str, new_id: str) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(update(MemoryRow).where(MemoryRow.id == old_id).values(superseded_by=new_id))

    async def forget(self, tenant_id: str, user_id: str, *, subject=None, memory_id=None, reason: str) -> list[Memory]:
        cond = [MemoryRow.tenant_id == tenant_id, MemoryRow.user_id == user_id, MemoryRow.active.is_(True)]
        if memory_id:
            cond.append(MemoryRow.id == memory_id)
        if subject:
            cond.append(MemoryRow.subject == subject)
        async with self._engine.begin() as conn:
            rows = [_to_memory(r) for r in await conn.execute(select(*MEMORY_COLUMNS).where(*cond))]
            if rows:
                await conn.execute(update(MemoryRow).where(MemoryRow.id.in_([m.id for m in rows])).values(active=False, deleted_at=datetime.now(UTC), deleted_reason=reason))
        return [Memory(**{**m.__dict__, "active": False, "deleted_reason": reason}) for m in rows]

    async def history(self, tenant_id: str, user_id: str) -> list[Memory]:
        async with self._engine.connect() as conn:
            rows = await conn.execute(select(*MEMORY_COLUMNS).where(MemoryRow.tenant_id == tenant_id, MemoryRow.user_id == user_id).order_by(MemoryRow.created_at))
        return [_to_memory(r) for r in rows]

    async def count(self) -> int:
        async with self._engine.connect() as conn:
            return int(await conn.scalar(select(func.count()).select_from(MemoryRow)) or 0)
