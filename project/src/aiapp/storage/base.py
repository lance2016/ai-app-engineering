"""The storage protocol every thread store implements."""

from typing import Protocol

from aiapp.thread import Thread


class ThreadNotFound(LookupError):
    """No such thread for this tenant. Deliberately the same error whether the id is unknown or belongs to someone else."""


class ThreadStore(Protocol):
    async def create(self, tenant_id: str) -> Thread: ...

    async def load(self, thread_id: str, *, tenant_id: str) -> Thread:
        """Raise ThreadNotFound if the thread does not exist or belongs to another tenant."""
        ...

    async def save(self, thread: Thread) -> None: ...
