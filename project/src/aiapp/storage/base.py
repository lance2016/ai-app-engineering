"""Storage protocols: the event-thread store and the small key-value store for coordination.

Two rules shape every implementation:

* ``load`` returns a snapshot. Mutating it changes nothing until ``append`` is
  called, and ``append`` carries the sequence number the caller *expects* to
  write. Two writers racing on one thread: one wins, one gets ``SeqConflict``.
* The key-value store (Redis in production) holds only things that may vanish:
  idempotency claims and the "a run is in progress" lock. Facts live in the
  thread store.
"""

from typing import Protocol

from aiapp.thread import Event, Thread


class ThreadNotFound(LookupError):
    """No such thread for this tenant. Deliberately the same error whether the id is unknown or belongs to someone else."""


class SeqConflict(RuntimeError):
    """Another writer appended to this thread first. Reload and decide again."""


class InvalidTransition(ValueError):
    """The event sequence is not allowed, e.g. an assistant_message right after human_input_requested."""


def check_transition(previous: Event | None, new: Event) -> None:
    """The one storage-level invariant M2 enforces. Stores call it (and PostgreSQL also has a trigger)."""
    if previous is not None and previous.type == "human_input_requested" and new.type == "assistant_message":
        raise InvalidTransition("assistant_message cannot follow human_input_requested; the human must answer first")


class ThreadStore(Protocol):
    async def create(self, tenant_id: str) -> Thread: ...

    async def load(self, thread_id: str, *, tenant_id: str) -> Thread:
        """A snapshot of the thread. Raise ThreadNotFound if it does not exist or belongs to another tenant."""
        ...

    async def append(self, thread_id: str, event: Event, *, expected_seq: int) -> None:
        """Persist one event at position ``expected_seq``. Raise SeqConflict if that position is taken."""
        ...


class KeyValueStore(Protocol):
    """Just enough of Redis for M2: claim-once keys with a TTL, read/write a small value, release a lock you hold."""

    async def claim(self, key: str, value: str, ttl_s: int) -> bool:
        """SET NX EX. True if this call created the key."""
        ...

    async def get(self, key: str) -> str | None: ...

    async def set(self, key: str, value: str, ttl_s: int) -> None: ...

    async def release(self, key: str, value: str) -> bool:
        """Delete the key only if it still holds ``value`` (so you never release someone else's lock)."""
        ...


async def flush(store: ThreadStore, thread: Thread, persisted: int) -> int:
    """Append every in-memory event past ``persisted``; return the new persisted count."""
    for seq in range(persisted, len(thread.events)):
        await store.append(thread.thread_id, thread.events[seq], expected_seq=seq)
    return len(thread.events)
