"""Failure injection wrappers. Used by tests and by AIAPP_INJECT to rehearse failures on purpose."""

import asyncio
from collections.abc import AsyncIterator

from aiapp.adapters.base import Message, ModelAdapter, ModelResponse, StreamChunk, ToolSpec


class SlowAdapter:
    """Delays every call; with a delay longer than the timeout it triggers the 504 path."""

    def __init__(self, inner: ModelAdapter, delay_s: float):
        self._inner = inner
        self.delay_s = delay_s
        self.name = f"slow({inner.name})"

    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse:
        await asyncio.sleep(self.delay_s)
        return await self._inner.complete(messages, tools)

    async def stream(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> AsyncIterator[StreamChunk]:
        await asyncio.sleep(self.delay_s)
        async for chunk in self._inner.stream(messages, tools):
            yield chunk


class ProviderDown(RuntimeError):
    pass


class FailingAdapter:
    """Raises on every call, standing in for a provider outage."""

    def __init__(self, inner: ModelAdapter, message: str = "provider returned 503"):
        self._inner = inner
        self.message = message
        self.name = f"failing({inner.name})"

    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse:
        raise ProviderDown(self.message)

    async def stream(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> AsyncIterator[StreamChunk]:
        raise ProviderDown(self.message)
        yield  # pragma: no cover - makes this an async generator


INJECTIONS = {
    "slow_model": lambda inner: SlowAdapter(inner, delay_s=10.0),
    "provider_error": lambda inner: FailingAdapter(inner),
}


def apply_injection(adapter: ModelAdapter, inject: str | None) -> ModelAdapter:
    if not inject:
        return adapter
    if inject not in INJECTIONS:
        raise ValueError(f"unknown AIAPP_INJECT={inject!r}; choose one of {sorted(INJECTIONS)}")
    return INJECTIONS[inject](adapter)
