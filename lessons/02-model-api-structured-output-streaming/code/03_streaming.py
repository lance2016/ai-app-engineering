"""Streaming changes what the user feels, not what the model computes.

Time-to-first-token is what a person notices; total time is what you pay.
Tool calls cannot be acted on until the arguments are complete, so they
arrive on the final chunk. The loop below prints deltas with timestamps so
both facts are visible.

Run:  uv run python lessons/02-model-api-structured-output-streaming/code/03_streaming.py
      INJECT_SLOW=1 uv run python lessons/02-model-api-structured-output-streaming/code/03_streaming.py
      MODEL_PROVIDER=deepseek uv run python lessons/02-model-api-structured-output-streaming/code/03_streaming.py
Expect: text arriving in pieces, then one final chunk with usage (and tool
        calls, if any). With INJECT_SLOW the gap between chunks is visible.
"""

# %% imports
import asyncio
import os
import time

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, get_adapter, tool_call_response

INJECT_SLOW = os.environ.get("INJECT_SLOW") == "1"
SPEC = ToolSpec("get_weather", "Current weather for a city.", {"type": "object", "properties": {"city": {"type": "string"}}})


# %% consume_stream
async def run(model, messages: list[Message]) -> None:
    started = time.monotonic()
    first_token_at = None
    text = []
    async for chunk in model.stream(messages, tools=[SPEC]):
        now = time.monotonic() - started
        if chunk.delta:
            if first_token_at is None:
                first_token_at = now
            text.append(chunk.delta)
            print(f"{now:6.3f}s  +{chunk.delta!r}")
        if chunk.done:
            print(f"{now:6.3f}s  [done] tool_calls={[c.name for c in chunk.tool_calls]} usage={chunk.usage}")
    total = time.monotonic() - started
    print(f"\nfirst token after {first_token_at or total:.3f}s, complete after {total:.3f}s, {len(''.join(text))} chars")


# %% run
async def main() -> None:
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    if provider == "fake":
        model = FakeAdapter(
            script=[ModelResponse(content="Shenzhen is sunny, 31 degrees, light breeze from the south.")],
            chunk_size=6,
            chunk_delay=0.15 if INJECT_SLOW else 0.0,
        )
    else:
        model = get_adapter(provider)
    await run(model, [Message(role="user", content="Describe the weather in Shenzhen in one sentence, no tools.")])
    print("\na UI shows chunks as they come; a tool runner must wait for the final chunk. same stream, two consumers.")


if __name__ == "__main__":
    asyncio.run(main())
