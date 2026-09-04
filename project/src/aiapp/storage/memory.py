"""Process-local implementations. Same contract as PostgreSQL and Redis, gone on restart."""

import time
from dataclasses import dataclass, field

from aiapp.storage.base import SeqConflict, ThreadNotFound, check_transition
from aiapp.thread import Event, Thread


@dataclass
class _Stored:
    tenant_id: str
    events: list[Event] = field(default_factory=list)


class InMemoryThreadStore:
    def __init__(self) -> None:
        self._threads: dict[str, _Stored] = {}

    async def create(self, tenant_id: str) -> Thread:
        thread = Thread()
        self._threads[thread.thread_id] = _Stored(tenant_id=tenant_id)
        return thread

    async def load(self, thread_id: str, *, tenant_id: str) -> Thread:
        stored = self._threads.get(thread_id)
        if stored is None or stored.tenant_id != tenant_id:
            raise ThreadNotFound(thread_id)
        return Thread(thread_id=thread_id, events=list(stored.events))  # a snapshot, like a row set from a database

    async def append(self, thread_id: str, event: Event, *, expected_seq: int) -> None:
        stored = self._threads.get(thread_id)
        if stored is None:
            raise ThreadNotFound(thread_id)
        if len(stored.events) != expected_seq:
            raise SeqConflict(f"thread {thread_id}: expected seq {expected_seq}, store has {len(stored.events)}")
        check_transition(stored.events[-1] if stored.events else None, event)
        stored.events.append(event)


class InMemoryKeyValueStore:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}  # key -> (value, expires_at)

    def _alive(self, key: str) -> str | None:
        item = self._data.get(key)
        if item is None:
            return None
        value, expires_at = item
        if expires_at <= time.monotonic():
            del self._data[key]
            return None
        return value

    async def claim(self, key: str, value: str, ttl_s: int) -> bool:
        if self._alive(key) is not None:
            return False
        self._data[key] = (value, time.monotonic() + ttl_s)
        return True

    async def get(self, key: str) -> str | None:
        return self._alive(key)

    async def set(self, key: str, value: str, ttl_s: int) -> None:
        self._data[key] = (value, time.monotonic() + ttl_s)

    async def release(self, key: str, value: str) -> bool:
        if self._alive(key) != value:
            return False
        del self._data[key]
        return True
