"""A minimal FastAPI SSE endpoint, self-tested in-process.

Server-sent events are the simplest way to stream agent output to a browser:
one HTTP response, `text/event-stream`, one `data:` line per delta. The test
client below drives the app without starting a server, so this file runs in
CI like every other sample.

Run:  uv run python lessons/16-system-architecture/code/02_sse_endpoint.py
Expect: the SSE body printed line by line, then a `done` event. Without fastapi
        installed the script explains how to get it and exits cleanly.
"""

# %% imports
import asyncio
import json
from collections.abc import AsyncIterator

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    from fastapi.testclient import TestClient
except ImportError:
    print("fastapi is not installed. Run `uv sync --group prereq` and try again.")
    raise SystemExit(0)

from aiapp import FakeAdapter, Message, ModelResponse

app = FastAPI()
MODEL = FakeAdapter(script=[ModelResponse(content="Refunds are accepted within thirty days of purchase.")])


# %% endpoint
async def agent_events(question: str) -> AsyncIterator[str]:
    """Yield SSE frames. A real run would stream token deltas and tool events from the thread."""
    reply = await MODEL.complete([Message(role="user", content=question)])
    for i, word in enumerate(reply.content.split()):
        await asyncio.sleep(0.01)
        yield f"id: {i}\nevent: delta\ndata: {json.dumps(word + ' ')}\n\n"
    yield "event: done\ndata: {}\n\n"


@app.get("/chat")
async def chat(q: str) -> StreamingResponse:
    return StreamingResponse(
        agent_events(q),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},  # keep proxies from buffering
    )


# %% self_test
def main() -> None:
    with TestClient(app) as client:
        with client.stream("GET", "/chat", params={"q": "refund window?"}) as response:
            assert response.headers["content-type"].startswith("text/event-stream")
            frames = 0
            for line in response.iter_lines():
                if line:
                    print(line)
                if line.startswith("event: done"):
                    frames += 1
    print(f"stream closed cleanly; done events: {frames}")


if __name__ == "__main__":
    main()
