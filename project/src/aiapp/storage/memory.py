"""Process-local thread store: a dict. Enough for M1's tests; gone on restart, which M2 fixes."""

from dataclasses import dataclass

from aiapp.storage.base import ThreadNotFound
from aiapp.thread import Thread


@dataclass
class _Stored:
    tenant_id: str
    thread: Thread


class InMemoryThreadStore:
    def __init__(self) -> None:
        self._threads: dict[str, _Stored] = {}

    async def create(self, tenant_id: str) -> Thread:
        thread = Thread()
        self._threads[thread.thread_id] = _Stored(tenant_id=tenant_id, thread=thread)
        return thread

    async def load(self, thread_id: str, *, tenant_id: str) -> Thread:
        stored = self._threads.get(thread_id)
        if stored is None or stored.tenant_id != tenant_id:
            raise ThreadNotFound(thread_id)
        return stored.thread

    async def save(self, thread: Thread) -> None:
        # The stored object *is* the live object; nothing to write. Kept so callers
        # do not change when the PostgreSQL store arrives in M2.
        if thread.thread_id not in self._threads:
            raise ThreadNotFound(thread.thread_id)

    def tenant_of(self, thread_id: str) -> str:
        return self._threads[thread_id].tenant_id
