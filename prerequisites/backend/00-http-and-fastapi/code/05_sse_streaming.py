"""Server-Sent Events: the server keeps writing, the client reads line by line.

This is how chat UIs show tokens as they arrive.

Run:  uv run python prerequisites/backend/00-http-and-fastapi/code/05_sse_streaming.py
Expect: the content-type is text/event-stream and five data lines arrive one at a time.
"""

# %% imports
import asyncio
import sys

try:
    from fastapi import FastAPI
    from fastapi.responses import StreamingResponse
    from fastapi.testclient import TestClient
except ImportError:
    print("fastapi is not installed. Run: uv sync --all-groups")
    sys.exit(0)

# %% app
app = FastAPI()


async def token_stream():
    for word in ["Hello", "from", "the", "server", "[DONE]"]:
        await asyncio.sleep(0.05)
        yield f"data: {word}\n\n"  # SSE frame: 'data:' line + blank line


@app.get("/stream")
async def stream() -> StreamingResponse:
    return StreamingResponse(token_stream(), media_type="text/event-stream")


# %% client_reads_incrementally
client = TestClient(app)
with client.stream("GET", "/stream") as r:
    print(r.headers["content-type"])
    for line in r.iter_lines():
        if line:
            print("got:", line)
