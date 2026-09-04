"""A scripted model for offline lessons and tests.

Give it a list of responses and it returns them in order. When the script
runs out it echoes the last message. Every call is recorded in ``calls`` so
tests can assert what the model was shown.
"""

import asyncio
import uuid
from collections import deque
from collections.abc import AsyncIterator, Iterable
from typing import Any

from aiapp.adapters.base import Message, ModelResponse, StreamChunk, ToolCall, ToolSpec, Usage


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def tool_call_response(name: str, arguments: dict[str, Any], call_id: str | None = None) -> ModelResponse:
    """Build a response in which the model asks for one tool call."""
    call = ToolCall(id=call_id or f"call_{uuid.uuid4().hex[:8]}", name=name, arguments=arguments)
    return ModelResponse(tool_calls=(call,))


class FakeAdapter:
    name = "fake"

    def __init__(self, script: Iterable[ModelResponse] = (), *, chunk_size: int = 4, chunk_delay: float = 0.0):
        self._script: deque[ModelResponse] = deque(script)
        self.calls: list[list[Message]] = []
        self.chunk_size = chunk_size
        self.chunk_delay = chunk_delay  # seconds between chunks; >0 makes streaming visible

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> ModelResponse:
        self.calls.append(list(messages))
        prompt_tokens = sum(_estimate_tokens(m.content) for m in messages)
        if self._script:
            scripted = self._script.popleft()
            return ModelResponse(
                content=scripted.content,
                tool_calls=scripted.tool_calls,
                usage=Usage(prompt_tokens, _estimate_tokens(scripted.content) + 8 * len(scripted.tool_calls)),
            )
        last = messages[-1].content if messages else ""
        content = f"[fake] echo: {last}"
        return ModelResponse(content=content, usage=Usage(prompt_tokens, _estimate_tokens(content)))

    async def stream(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> AsyncIterator[StreamChunk]:
        """Replay a scripted response as small text increments, then a final chunk."""
        full = await self.complete(messages, tools)
        for i in range(0, len(full.content), self.chunk_size):
            if self.chunk_delay:
                await asyncio.sleep(self.chunk_delay)
            yield StreamChunk(delta=full.content[i : i + self.chunk_size])
        yield StreamChunk(done=True, tool_calls=full.tool_calls, usage=full.usage)
