"""The client watches the same event log the runtime writes.

Instead of inventing a second "progress" data structure, the loop yields each
event as it appends it. A UI, a log shipper or a test can consume the stream;
what the user sees and what gets persisted can never disagree.

Run:  uv run python lessons/07-agent-state-and-runtime/code/03_event_stream.py
Expect: events printed as they happen, formatted like server-sent events,
        and a final thread whose event list equals what was streamed.
"""

# %% imports
import asyncio
import json
from collections.abc import AsyncIterator

from aiapp import Event, FakeAdapter, ModelResponse, Thread, ToolSpec, tool_call_response, tool_calls_as_data

SEARCH = ToolSpec("search", "Search.", {"type": "object", "properties": {"q": {"type": "string"}}})


# %% streaming_loop
async def run_streaming(thread: Thread, model: FakeAdapter) -> AsyncIterator[Event]:
    """Same loop as before; every append is also yielded to whoever is listening."""
    yield thread.append("run_started")
    for _ in range(6):
        reply = await model.complete(thread.to_messages(), tools=[SEARCH])
        yield thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
        if not reply.wants_tool:
            yield thread.append("run_finished", answer=reply.content)
            return
        for call in reply.tool_calls:
            await asyncio.sleep(0.05)  # pretend the tool takes time; the client sees progress meanwhile
            yield thread.append("tool_result", tool_call_id=call.id, content=f"results for {call.arguments['q']}")


# %% client
def as_sse(event: Event) -> str:
    return f"event: {event.type}\ndata: {json.dumps(event.data, ensure_ascii=False)}\n"


# %% run
async def main() -> None:
    thread = Thread()
    thread.append("user_message", content="Compare two laptops for me.")
    model = FakeAdapter(script=[
        tool_call_response("search", {"q": "laptop A specs"}),
        tool_call_response("search", {"q": "laptop B specs"}),
        ModelResponse(content="A is lighter, B has the better screen."),
    ])
    streamed: list[Event] = []
    async for event in run_streaming(thread, model):
        streamed.append(event)
        print(as_sse(event))
    assert streamed == thread.events[1:], "stream and log diverged"
    print(f"streamed {len(streamed)} events; thread has {len(thread.events)} (plus the initial user message)")


if __name__ == "__main__":
    asyncio.run(main())
