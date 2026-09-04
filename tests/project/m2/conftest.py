"""M2 fixtures. The same contract tests run against in-memory and real backends.

Real backends are used when reachable (docker compose up -d), skipped otherwise.
DATABASE_URL / REDIS_URL override the compose defaults; CI sets them explicitly.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

from aiapp.storage.memory import InMemoryKeyValueStore, InMemoryThreadStore

ROOT = Path(__file__).resolve().parents[3]
ALEMBIC_INI = ROOT / "project/src/aiapp/storage/alembic.ini"
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _in_fresh_loop(coro_factory):
    """Run a coroutine on its own loop in a worker thread: these probes may be called while a test loop is already running."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(coro_factory())).result()


def _postgres_reachable() -> bool:
    import asyncpg

    async def probe() -> None:
        conn = await asyncpg.connect(DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://"), timeout=1.5)
        await conn.close()

    try:
        _in_fresh_loop(probe)
        return True
    except Exception:
        return False


def _redis_reachable() -> bool:
    from redis.asyncio import Redis

    async def probe() -> None:
        client = Redis.from_url(REDIS_URL, socket_connect_timeout=1.5)
        try:
            await client.ping()
        finally:
            await client.aclose()

    try:
        _in_fresh_loop(probe)
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def postgres_url() -> str:
    if not _postgres_reachable():
        pytest.skip(f"PostgreSQL not reachable at {DATABASE_URL}; run `docker compose up -d`")
    os.environ["DATABASE_URL"] = DATABASE_URL
    with ThreadPoolExecutor(max_workers=1) as pool:  # alembic's env.py uses asyncio.run; keep it off the test loop
        pool.submit(command.upgrade, Config(str(ALEMBIC_INI)), "head").result()
    return DATABASE_URL


@pytest.fixture(scope="session")
def redis_url() -> str:
    if not _redis_reachable():
        pytest.skip(f"Redis not reachable at {REDIS_URL}; run `docker compose up -d`")
    return REDIS_URL


@pytest.fixture(params=["memory", "postgres"])
async def thread_store(request):
    if request.param == "memory":
        yield InMemoryThreadStore()
        return
    from aiapp.storage.postgres import PostgresThreadStore

    store = PostgresThreadStore.from_url(request.getfixturevalue("postgres_url"))
    yield store
    await store.dispose()


@pytest.fixture(params=["memory", "redis"])
async def kv_store(request):
    if request.param == "memory":
        yield InMemoryKeyValueStore()
        return
    from aiapp.storage.redis_kv import RedisKeyValueStore

    kv = RedisKeyValueStore.from_url(request.getfixturevalue("redis_url"))
    yield kv
    await kv.close()
