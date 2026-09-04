"""PostgreSQL thread store. Events are rows; the unique (conversation_id, seq) index is the optimistic lock."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from aiapp.storage.base import InvalidTransition, SeqConflict, ThreadNotFound, check_transition
from aiapp.storage.models import Conversation, Message, Task
from aiapp.thread import Event, Thread

STATUS_BY_EVENT = {
    "run_started": "running",
    "human_input_requested": "paused",
    "human_input": "running",
    "run_finished": "finished",
    "run_failed": "failed",
}


def _pgcode(exc: IntegrityError) -> str | None:
    return getattr(exc.orig, "pgcode", None) or getattr(getattr(exc.orig, "__cause__", None), "sqlstate", None)


class PostgresThreadStore:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    @classmethod
    def from_url(cls, url: str) -> "PostgresThreadStore":
        return cls(create_async_engine(url, pool_pre_ping=True))

    async def dispose(self) -> None:
        await self._engine.dispose()

    async def create(self, tenant_id: str) -> Thread:
        thread = Thread()
        async with self._engine.begin() as conn:
            await conn.execute(insert(Conversation).values(id=thread.thread_id, tenant_id=tenant_id, status="new"))
        return thread

    async def load(self, thread_id: str, *, tenant_id: str) -> Thread:
        async with self._engine.connect() as conn:
            owner = await conn.scalar(select(Conversation.tenant_id).where(Conversation.id == thread_id))
            if owner is None or owner != tenant_id:
                raise ThreadNotFound(thread_id)
            rows = await conn.execute(
                select(Message.type, Message.data, Message.created_at).where(Message.conversation_id == thread_id).order_by(Message.seq)
            )
        events = [Event(type=t, data=d, ts=created.timestamp()) for t, d, created in rows]
        return Thread(thread_id=thread_id, events=events)

    async def append(self, thread_id: str, event: Event, *, expected_seq: int) -> None:
        async with self._engine.begin() as conn:
            previous = await conn.execute(
                select(Message.type, Message.data, Message.created_at)
                .where(Message.conversation_id == thread_id, Message.seq == expected_seq - 1)
            )
            prev_row = previous.first()
            check_transition(Event(type=prev_row[0], data=prev_row[1], ts=prev_row[2].timestamp()) if prev_row else None, event)
            try:
                await conn.execute(
                    insert(Message).values(
                        conversation_id=thread_id,
                        seq=expected_seq,
                        type=event.type,
                        data=event.data,
                        created_at=datetime.fromtimestamp(event.ts, tz=UTC),
                    )
                )
            except IntegrityError as exc:
                code = _pgcode(exc)
                if code == "23505":  # unique_violation: someone else took this seq
                    raise SeqConflict(f"thread {thread_id}: seq {expected_seq} already written") from None
                if code == "23514":  # check_violation: the trigger fired
                    raise InvalidTransition(str(exc.orig)) from None
                if code == "23503":  # foreign_key_violation: no such conversation
                    raise ThreadNotFound(thread_id) from None
                raise
            await self._bookkeep(conn, thread_id, event)

    async def _bookkeep(self, conn, thread_id: str, event: Event) -> None:
        """Caches derived from the log: conversation.status and the task table."""
        status = STATUS_BY_EVENT.get(event.type)
        if status:
            await conn.execute(update(Conversation).where(Conversation.id == thread_id).values(status=status))
        when = datetime.fromtimestamp(event.ts, tz=UTC)
        if event.type == "run_started":
            await conn.execute(insert(Task).values(id=f"task_{uuid.uuid4().hex[:8]}", conversation_id=thread_id, started_at=when))
        elif event.type in ("run_finished", "run_failed"):
            usage = event.data.get("usage") or {}
            open_task = (
                select(Task.id).where(Task.conversation_id == thread_id, Task.finished_at.is_(None)).order_by(Task.started_at.desc()).limit(1)
            ).scalar_subquery()
            await conn.execute(
                update(Task)
                .where(Task.id == open_task)
                .values(
                    finished_at=when,
                    stop_reason=event.data.get("reason", "finished") if event.type == "run_failed" else "finished",
                    tokens_in=usage.get("input_tokens", 0),
                    tokens_out=usage.get("output_tokens", 0),
                )
            )
