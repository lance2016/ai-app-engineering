"""Provider-neutral message and tool types plus the adapter protocol.

Every lesson talks to the model through ``ModelAdapter``. Real providers
(OpenAI, Anthropic, DashScope, ...) are wrapped behind this protocol in
lesson 02; ``FakeAdapter`` implements it for offline runs.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class ToolCall:
    """The model's *request* to run a tool. Nothing has happened yet."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None  # set on role="tool" messages
    is_error: bool = False  # tool result that reports a failure


@dataclass(frozen=True)
class ToolSpec:
    """What the model is told about a tool. ``parameters`` is JSON Schema."""

    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class ModelResponse:
    content: str = ""
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage = field(default_factory=Usage)

    @property
    def wants_tool(self) -> bool:
        return bool(self.tool_calls)


@dataclass(frozen=True)
class StreamChunk:
    """One increment of a streamed response.

    ``delta`` carries new text. Tool calls and usage are only known once the
    provider has finished, so they arrive on the final chunk (``done=True``).
    """

    delta: str = ""
    done: bool = False
    tool_calls: tuple[ToolCall, ...] = ()
    usage: Usage | None = None


class ModelAdapter(Protocol):
    name: str

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> ModelResponse: ...

    def stream(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> AsyncIterator[StreamChunk]: ...
