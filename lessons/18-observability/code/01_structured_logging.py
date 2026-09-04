"""Logs you can query: one JSON object per line, with a correlation id on every line.

Free-text logs answer "what did the process print". Structured logs answer
"show me every step of run r_42 where tokens > 1000". The difference is a
formatter and the discipline of passing the same run_id everywhere.

Run:  uv run python lessons/18-observability/code/01_structured_logging.py
Expect: JSON lines for one agent run, then a one-line 'query' over them showing
        how a correlation id turns a log stream into a per-run story.
"""

# %% imports
import asyncio
import json
import logging
import sys
import time
import uuid

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response


# %% json_formatter
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": round(record.created, 3), "level": record.levelname, "event": record.getMessage()}
        payload.update(getattr(record, "fields", {}))  # structured fields ride along in `extra`
        return json.dumps(payload, ensure_ascii=False)


def make_logger() -> logging.Logger:
    logger = logging.getLogger("aiapp.lesson18")
    logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log(logger: logging.Logger, event: str, **fields) -> None:
    logger.info(event, extra={"fields": fields})


# %% instrumented_run
SEARCH = ToolSpec("search", "Search.", {"type": "object", "properties": {"q": {"type": "string"}}})


async def run(logger: logging.Logger) -> None:
    run_id = f"r_{uuid.uuid4().hex[:6]}"
    model = FakeAdapter(script=[tool_call_response("search", {"q": "laptops"}), ModelResponse(content="Two options found.")])
    messages = [Message(role="user", content="Find laptops")]
    log(logger, "run.start", run_id=run_id, user_len=len(messages[0].content))
    for step in range(1, 5):
        t0 = time.perf_counter()
        reply = await model.complete(messages, tools=[SEARCH])
        log(logger, "model.call", run_id=run_id, step=step, latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            input_tokens=reply.usage.input_tokens, output_tokens=reply.usage.output_tokens, wants_tool=reply.wants_tool)
        if not reply.wants_tool:
            log(logger, "run.finish", run_id=run_id, steps=step, answer_len=len(reply.content))
            return
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            log(logger, "tool.call", run_id=run_id, step=step, tool=call.name, args=call.arguments)
            messages.append(Message(role="tool", tool_call_id=call.id, content="3 results"))


# %% query_the_stream
async def main() -> None:
    logger = make_logger()
    await run(logger)
    print("\n-- the same lines, queried as data (what a log platform does for you) --")
    # Re-run into a buffer to demonstrate filtering without a log platform.
    buffer: list[dict] = []
    logger.handlers[0].stream = type("Sink", (), {"write": lambda self, s: buffer.append(json.loads(s)) if s.strip() else None, "flush": lambda self: None})()
    await run(logger)
    run_id = buffer[0]["run_id"]
    steps = [b for b in buffer if b["run_id"] == run_id and b["event"] == "model.call"]
    print(f"run {run_id}: {len(steps)} model calls, total input tokens {sum(s['input_tokens'] for s in steps)}")


if __name__ == "__main__":
    asyncio.run(main())
