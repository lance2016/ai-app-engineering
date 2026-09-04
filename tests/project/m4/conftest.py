"""M4 fixtures: the sample corpus and golden set, knowledge and memory stores on memory and PostgreSQL."""

import json
from pathlib import Path

import pytest

from aiapp.adapters.embeddings import HashingEmbedding
from aiapp.knowledge import Retriever, parse_markdown
from aiapp.knowledge.memory import InMemoryMemoryStore
from aiapp.knowledge.memory_store import InMemoryKnowledgeStore

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "project/m4-rag-and-memory/docs-sample"
GOLDEN = [json.loads(l) for l in (ROOT / "project/m4-rag-and-memory/golden/qa.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def load_docs() -> list:
    return [parse_markdown(p.stem, p.read_text(encoding="utf-8")) for p in sorted(DOCS.glob("*.md"))]


@pytest.fixture(params=["memory", "postgres"])
async def knowledge_store(request):
    if request.param == "memory":
        yield InMemoryKnowledgeStore()
        return
    from aiapp.knowledge.postgres_store import PostgresKnowledgeStore

    store = PostgresKnowledgeStore.from_url(request.getfixturevalue("postgres_url"))
    yield store
    await store.dispose()


@pytest.fixture(params=["memory", "postgres"])
async def memory_store(request):
    if request.param == "memory":
        yield InMemoryMemoryStore()
        return
    from aiapp.knowledge.postgres_memory import PostgresMemoryStore

    store = PostgresMemoryStore.from_url(request.getfixturevalue("postgres_url"))
    yield store
    await store.dispose()


@pytest.fixture
def embedder() -> HashingEmbedding:
    return HashingEmbedding()


@pytest.fixture
def retriever(knowledge_store, embedder) -> Retriever:
    return Retriever(knowledge_store, embedder)


def tenant() -> str:
    import uuid

    return f"t-{uuid.uuid4().hex[:8]}"  # a fresh tenant per test keeps the shared PostgreSQL database clean


from tests.project.m2.conftest import postgres_url, redis_url  # noqa: E402,F401  (session fixtures shared with M2)
