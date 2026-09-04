"""Shared fixtures for the M1 acceptance tests. Everything runs in-process against the fake model."""

import asyncio
from collections.abc import AsyncIterator, Iterable

import pytest
from fastapi.testclient import TestClient

from aiapp import FakeAdapter, ModelResponse
from aiapp.adapters.base import Message, ModelAdapter, StreamChunk, ToolSpec
from aiapp.api import create_app
from aiapp.config import Settings

TOKENS = {"token-a": "tenant-a", "token-b": "tenant-b"}
AUTH_A = {"Authorization": "Bearer token-a"}
AUTH_B = {"Authorization": "Bearer token-b"}


def make_settings(**overrides) -> Settings:
    base = {"tokens": TOKENS, "model_timeout_s": 0.3}
    return Settings(**{**base, **overrides})


def make_client(*, script: Iterable[ModelResponse] = (), model: ModelAdapter | None = None, **settings) -> TestClient:
    model = model or FakeAdapter(script=list(script) or [ModelResponse(content="Hello from the fake model.")], chunk_size=6)
    app = create_app(settings=make_settings(**settings), model=model)
    client = TestClient(app, raise_server_exceptions=False)
    client.model = model  # type: ignore[attr-defined]
    return client


class StallingAdapter:
    """Streams one chunk, then never sends another: the mid-stream timeout path."""

    name = "stalling"

    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse:
        return ModelResponse(content="never used")

    async def stream(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(delta="Once upon")
        await asyncio.sleep(10)
        yield StreamChunk(done=True)


def parse_sse(text: str) -> list[tuple[str, dict]]:
    """[(event_type, data_dict), ...] from a raw text/event-stream body."""
    frames = []
    for block in text.strip().split("\n\n"):
        event, data = None, None
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[len("event: ") :]
            elif line.startswith("data: "):
                data = __import__("json").loads(line[len("data: ") :])
        if event is not None:
            frames.append((event, data or {}))
    return frames


@pytest.fixture
def client() -> TestClient:
    return make_client()


@pytest.fixture
def thread_id(client: TestClient) -> str:
    return client.post("/v1/threads", json={}, headers=AUTH_A).json()["thread_id"]
