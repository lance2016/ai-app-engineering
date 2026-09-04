"""Adapter for any provider that speaks the OpenAI chat-completions protocol.

DeepSeek, DashScope (Qwen) and OpenAI itself all expose this shape; only the
base URL, key and model name differ. The adapter translates between the
course's provider-neutral types and the wire format in both directions.
"""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass

from openai import AsyncOpenAI

from aiapp.adapters.base import Message, ModelResponse, StreamChunk, ToolCall, ToolSpec, Usage


@dataclass(frozen=True)
class ProviderPreset:
    base_url: str
    key_env: str
    default_model: str


PRESETS: dict[str, ProviderPreset] = {
    "deepseek": ProviderPreset("https://api.deepseek.com", "DEEPSEEK_API_KEY", "deepseek-chat"),
    "dashscope": ProviderPreset("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "qwen-plus"),
    "openai": ProviderPreset("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
}


def _to_wire(message: Message) -> dict:
    if message.role == "tool":
        content = f"ERROR: {message.content}" if message.is_error else message.content
        return {"role": "tool", "tool_call_id": message.tool_call_id, "content": content}
    if message.role == "assistant" and message.tool_calls:
        return {
            "role": "assistant",
            "content": message.content or None,
            "tool_calls": [
                {"id": c.id, "type": "function", "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                for c in message.tool_calls
            ],
        }
    return {"role": message.role, "content": message.content}


def _tool_to_wire(spec: ToolSpec) -> dict:
    return {"type": "function", "function": {"name": spec.name, "description": spec.description, "parameters": spec.parameters}}


def _parse_arguments(raw: str) -> dict:
    """Providers return arguments as a JSON string; a malformed one is still a tool call."""
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {"_raw": raw}
    return parsed if isinstance(parsed, dict) else {"_raw": raw}


class OpenAICompatibleAdapter:
    def __init__(self, *, name: str, api_key: str, base_url: str, model: str):
        self.name = name
        self.model = model
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def complete(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> ModelResponse:
        kwargs = {"tools": [_tool_to_wire(t) for t in tools]} if tools else {}
        completion = await self._client.chat.completions.create(
            model=self.model, messages=[_to_wire(m) for m in messages], **kwargs
        )
        choice = completion.choices[0].message
        calls = tuple(
            ToolCall(id=c.id, name=c.function.name, arguments=_parse_arguments(c.function.arguments))
            for c in (choice.tool_calls or [])
        )
        usage = completion.usage
        return ModelResponse(
            content=choice.content or "",
            tool_calls=calls,
            usage=Usage(usage.prompt_tokens, usage.completion_tokens) if usage else Usage(),
        )

    async def stream(
        self, messages: list[Message], tools: list[ToolSpec] | None = None
    ) -> AsyncIterator[StreamChunk]:
        """Yield text deltas as they arrive; assemble tool calls and usage for the final chunk."""
        kwargs = {"tools": [_tool_to_wire(t) for t in tools]} if tools else {}
        response = await self._client.chat.completions.create(
            model=self.model,
            messages=[_to_wire(m) for m in messages],
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )
        partial: dict[int, dict] = {}  # tool call index -> {id, name, arguments (str)}
        usage = None
        async for event in response:
            if event.usage:
                usage = Usage(event.usage.prompt_tokens, event.usage.completion_tokens)
            if not event.choices:
                continue
            delta = event.choices[0].delta
            if delta.content:
                yield StreamChunk(delta=delta.content)
            for tc in delta.tool_calls or []:
                slot = partial.setdefault(tc.index, {"id": "", "name": "", "arguments": ""})
                if tc.id:
                    slot["id"] = tc.id
                if tc.function and tc.function.name:
                    slot["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    slot["arguments"] += tc.function.arguments
        calls = tuple(
            ToolCall(id=slot["id"], name=slot["name"], arguments=_parse_arguments(slot["arguments"]))
            for _, slot in sorted(partial.items())
        )
        yield StreamChunk(done=True, tool_calls=calls, usage=usage)
