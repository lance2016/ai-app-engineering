"""Every KeyValueStore implementation must pass these. Runs on memory and Redis."""

import asyncio
import uuid

import pytest

pytestmark = pytest.mark.anyio


def key(prefix: str) -> str:
    return f"test:{prefix}:{uuid.uuid4().hex}"


async def test_claim_is_set_nx(kv_store) -> None:
    k = key("claim")
    assert await kv_store.claim(k, "owner-1", ttl_s=30) is True
    assert await kv_store.claim(k, "owner-2", ttl_s=30) is False
    assert await kv_store.get(k) == "owner-1"


async def test_release_only_by_the_owner(kv_store) -> None:
    k = key("lock")
    await kv_store.claim(k, "owner-1", ttl_s=30)
    assert await kv_store.release(k, "owner-2") is False, "someone else's token must not release the lock"
    assert await kv_store.get(k) == "owner-1"
    assert await kv_store.release(k, "owner-1") is True
    assert await kv_store.get(k) is None
    assert await kv_store.claim(k, "owner-2", ttl_s=30) is True


async def test_set_overwrites_and_ttl_expires(kv_store) -> None:
    k = key("ttl")
    await kv_store.set(k, "v1", ttl_s=30)
    await kv_store.set(k, "v2", ttl_s=1)
    assert await kv_store.get(k) == "v2"
    await asyncio.sleep(1.2)
    assert await kv_store.get(k) is None, "a key without a live TTL is a memory leak; every write carries one"
    assert await kv_store.claim(k, "owner", ttl_s=30) is True, "an expired lock can be claimed again"
