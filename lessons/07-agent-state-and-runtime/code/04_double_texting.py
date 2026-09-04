"""The user sends a second message while a run is still going. Now what?

Three deliberate policies, each a few lines once state lives in a thread:
reject the new message, enqueue it for after the current run, or interrupt
the run and start over with both messages while keeping the work done so far.
Picking none of them means picking "undefined behaviour".

Run:  uv run python lessons/07-agent-state-and-runtime/code/04_double_texting.py                 # default: interrupt
      DOUBLE_TEXT=reject  uv run python lessons/07-agent-state-and-runtime/code/04_double_texting.py
      DOUBLE_TEXT=enqueue uv run python lessons/07-agent-state-and-runtime/code/04_double_texting.py
Expect: each policy prints what happened to the first run and to the second message.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, ModelResponse, Thread, ToolSpec, tool_call_response, tool_calls_as_data

POLICY = os.environ.get("DOUBLE_TEXT", "interrupt")
SEARCH = ToolSpec("search", "Search.", {"type": "object", "properties": {"q": {"type": "string"}}})


# %% slow_run
async def run(thread: Thread, model: FakeAdapter) -> str:
    for _ in range(6):
        reply = await model.complete(thread.to_messages(), tools=[SEARCH])
        thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
        if not reply.wants_tool:
            thread.append("run_finished", answer=reply.content)
            return reply.content
        for call in reply.tool_calls:
            await asyncio.sleep(0.2)  # slow tool; the second message lands during this
            thread.append("tool_result", tool_call_id=call.id, content=f"results for {call.arguments['q']}")
    return "step limit"


def make_model(label: str) -> FakeAdapter:
    return FakeAdapter(script=[
        tool_call_response("search", {"q": f"{label} step 1"}),
        tool_call_response("search", {"q": f"{label} step 2"}),
        ModelResponse(content=f"{label}: here is the answer."),
    ])


# %% policies
async def handle_second_message(thread: Thread, current: asyncio.Task, text: str) -> None:
    if POLICY == "reject":
        print(f"reject: '{text}' dropped, first run continues")
        await current
    elif POLICY == "enqueue":
        print(f"enqueue: '{text}' waits for the first run")
        await current
        thread.append("user_message", content=text)
        print(f"second run answer: {await run(thread, make_model('run 2'))}")
    elif POLICY == "interrupt":
        current.cancel()
        try:
            await current
        except asyncio.CancelledError:
            pass
        done = sum(1 for e in thread.events if e.type == "tool_result")
        thread.append("run_interrupted", completed_tool_results=done)
        thread.append("user_message", content=text)
        print(f"interrupt: first run stopped after {done} tool result(s); work kept in the thread")
        print(f"second run answer: {await run(thread, make_model('run 2'))}")
    else:
        raise SystemExit(f"unknown DOUBLE_TEXT policy {POLICY!r}")


# %% run
async def main() -> None:
    thread = Thread()
    thread.append("user_message", content="Find me a laptop.")
    first = asyncio.create_task(run(thread, make_model("run 1")))
    await asyncio.sleep(0.3)  # first run is mid-way through its slow tool
    await handle_second_message(thread, first, "Actually, make it a tablet.")
    if first.done() and not first.cancelled():
        print(f"first run answer: {first.result()}")
    print(f"policy={POLICY} events={[e.type for e in thread.events]}")


if __name__ == "__main__":
    asyncio.run(main())
