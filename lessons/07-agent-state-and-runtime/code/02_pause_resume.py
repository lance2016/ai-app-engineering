"""Launch, pause, resume across separate processes.

Asking the human is a tool call. When the model uses it the runtime records
the request, checkpoints the thread to disk and exits. A later process loads
the thread, appends the human's answer and continues the same fold. Tool
calls that already have a result are never re-executed, so a crash between
steps is safe to recover from.

Run:  uv run python lessons/07-agent-state-and-runtime/code/02_pause_resume.py            # pauses
      USER_ANSWER="Sea Breeze" uv run python lessons/07-agent-state-and-runtime/code/02_pause_resume.py   # resumes, finishes
      INJECT_CRASH=1 uv run python lessons/07-agent-state-and-runtime/code/02_pause_resume.py   # dies after step 1
      uv run python lessons/07-agent-state-and-runtime/code/02_pause_resume.py            # recovers without re-running step 1
Expect: the checkpoint file carries the run between invocations; tool
        execution counts never exceed one per tool call.
"""

# %% imports
import asyncio
import os
import sys
import tempfile
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, Thread, ToolCall, ToolSpec, tool_call_response, tool_calls_as_data

CHECKPOINT = Path(os.environ.get("CHECKPOINT_DIR", tempfile.gettempdir())) / "aiapp_lesson07_thread.json"
USER_ANSWER = os.environ.get("USER_ANSWER")
INJECT_CRASH = os.environ.get("INJECT_CRASH") == "1"

TOOLS = [
    ToolSpec("find_restaurants", "Find restaurants.", {"type": "object", "properties": {"party": {"type": "integer"}}}),
    ToolSpec("request_human_input", "Ask the user a question and wait.", {"type": "object", "properties": {"question": {"type": "string"}}}),
    ToolSpec("book", "Book a table.", {"type": "object", "properties": {"name": {"type": "string"}}}),
]
EXECUTIONS: dict[str, int] = {}  # tool name -> how many times it actually ran (this process)


# %% execute_tool
def execute(call: ToolCall) -> str:
    EXECUTIONS[call.name] = EXECUTIONS.get(call.name, 0) + 1
    if call.name == "find_restaurants":
        return '["Noodle House", "Sea Breeze"]'
    if call.name == "book":
        return f"booked {call.arguments['name']} for tonight"
    raise ValueError(call.name)


# %% run_until_pause
async def run(thread: Thread, model: FakeAdapter, *, max_steps: int = 6) -> None:
    """Continue the fold from wherever the thread is. Returns on finish or pause."""
    while thread.steps() < max_steps:
        # 1. settle anything the model already asked for but that has no result yet
        for call in thread.pending_tool_calls():
            if call.name == "request_human_input":
                thread.append("human_input_requested", tool_call_id=call.id, question=call.arguments["question"])
                thread.save(CHECKPOINT)
                print(f"paused: {call.arguments['question']!r}  (checkpoint: {CHECKPOINT})")
                return
            thread.append("tool_result", tool_call_id=call.id, content=execute(call))
            thread.save(CHECKPOINT)  # checkpoint after every recorded result
            print(f"executed {call.name}")
            if INJECT_CRASH:
                print("!! simulated crash after step 1")
                sys.exit(1)
        # 2. ask the model for the next step
        reply = await model.complete(thread.to_messages(), tools=TOOLS)
        thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
        thread.save(CHECKPOINT)
        if not reply.wants_tool:
            thread.append("run_finished", answer=reply.content)
            thread.save(CHECKPOINT)
            print(f"finished: {reply.content}")
            return
    print("step limit")


# %% script_for_fake
def script_from(thread: Thread) -> list[ModelResponse]:
    """The fake model 'knows' the plan; a real one derives it from thread.to_messages()."""
    done = {e.data.get("tool_call_id") for e in thread.events if e.type == "tool_result"} | \
           {e.data.get("tool_call_id") for e in thread.events if e.type == "human_input"}
    plan = [
        ("c1", tool_call_response("find_restaurants", {"party": 2}, call_id="c1")),
        ("c2", tool_call_response("request_human_input", {"question": "Noodle House or Sea Breeze?"}, call_id="c2")),
        ("c3", tool_call_response("book", {"name": USER_ANSWER or "?"}, call_id="c3")),
    ]
    remaining = [r for cid, r in plan if cid not in done]
    return remaining + [ModelResponse(content=f"Done, {USER_ANSWER} is booked for two tonight.")]


# %% launch_or_resume
async def main() -> None:
    if CHECKPOINT.exists():
        thread = Thread.load(CHECKPOINT)
        print(f"resuming {thread.thread_id}: status={thread.status()} steps={thread.steps()}")
        if thread.status() == "finished":
            CHECKPOINT.unlink()
            print("previous run already finished; checkpoint cleared, run again to start fresh")
            return
        if thread.status() == "paused":
            if not USER_ANSWER:
                print("still waiting for the human. Set USER_ANSWER=... to resume.")
                return
            pending = thread.pending_tool_calls()[0]
            thread.append("human_input", tool_call_id=pending.id, content=USER_ANSWER)
    else:
        thread = Thread()
        thread.append("user_message", content="Book me a table for two tonight.")
        print(f"launching {thread.thread_id}")
    await run(thread, FakeAdapter(script=script_from(thread)))
    print(f"tool executions this process: {EXECUTIONS}")


if __name__ == "__main__":
    asyncio.run(main())
