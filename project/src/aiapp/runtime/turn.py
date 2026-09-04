"""One conversational turn without tools: append the user message, stream the model, record the result.

This is the M1 loop. M3 replaces it with the tool-running loop; the contract
stays: the caller gets an async iterator of thread events (persisted) and
``Delta`` items (transient text increments, streamed but not stored).

Timeouts: nothing is yielded until the model's first chunk has arrived, so a
timeout or provider error there propagates to the caller *before* any bytes
reach the client, and the caller can still answer with a proper status code.
After that, a stall between chunks ends the run with a ``run_failed`` event.
"""

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass

from aiapp.adapters.base import Message, ModelAdapter, StreamChunk, Usage
from aiapp.thread import Event, Thread


@dataclass(frozen=True)
class Delta:
    """A streamed text increment. Shown to the client, never stored: the thread keeps the whole message."""

    content: str


async def _next_chunk(stream: AsyncIterator[StreamChunk], timeout_s: float) -> StreamChunk:
    async with asyncio.timeout(timeout_s):
        return await anext(stream)


async def run_turn(
    thread: Thread,
    model: ModelAdapter,
    *,
    system_prompt: str,
    user_content: str,
    timeout_s: float,
) -> AsyncIterator[Event | Delta]:
    user_event = thread.append("user_message", content=user_content)
    started = thread.append("run_started", model=model.name)
    messages = [Message(role="system", content=system_prompt), *thread.to_messages()]
    stream = model.stream(messages)

    try:
        first = await _next_chunk(stream, timeout_s)
    except TimeoutError:
        thread.append("run_failed", reason="model_timeout", stage="first_chunk")
        raise
    except Exception as exc:
        thread.append("run_failed", reason="provider_error", stage="first_chunk", detail=str(exc))
        raise

    yield user_event
    yield started

    parts: list[str] = []
    usage: Usage | None = None
    chunk = first
    while True:
        if chunk.delta:
            parts.append(chunk.delta)
            yield Delta(chunk.delta)
        if chunk.done:
            usage = chunk.usage
            break
        try:
            chunk = await _next_chunk(stream, timeout_s)
        except StopAsyncIteration:
            break
        except TimeoutError:
            yield thread.append("run_failed", reason="model_timeout", stage="mid_stream", partial="".join(parts))
            return
        except Exception as exc:
            yield thread.append("run_failed", reason="provider_error", stage="mid_stream", detail=str(exc))
            return

    content = "".join(parts)
    yield thread.append("assistant_message", content=content, tool_calls=[])
    yield thread.append(
        "run_finished",
        answer=content,
        usage={"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None,
    )
