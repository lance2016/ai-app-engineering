"""Thread storage. M1 ships an in-memory store; M2 adds PostgreSQL behind the same protocol."""

from aiapp.storage.base import ThreadNotFound, ThreadStore
from aiapp.storage.memory import InMemoryThreadStore

__all__ = ["InMemoryThreadStore", "ThreadNotFound", "ThreadStore"]
