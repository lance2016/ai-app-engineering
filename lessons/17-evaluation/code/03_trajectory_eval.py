"""Judge the path, not only the destination. Record it, then replay it in tests.

An agent can reach the right answer by an unacceptable route: an extra tool
with side effects, a forbidden tool, too many steps, or the same call twice.
Trajectory assertions run over the lesson-07 Thread. The thread is also saved
as a JSON fixture so the same assertions run in CI without any model.

Run:  uv run python lessons/17-evaluation/code/03_trajectory_eval.py
      INJECT_DETOUR=1 uv run python lessons/17-evaluation/code/03_trajectory_eval.py
Expect: the clean run passes all trajectory checks and writes a fixture;
        the detour reaches the same final answer but fails "no unnecessary tools".
"""

# %% imports
import asyncio
import json
import os
import tempfile
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, Thread, ToolSpec, tool_call_response, tool_calls_as_data

INJECT_DETOUR = os.environ.get("INJECT_DETOUR") == "1"
FIXTURE = Path(os.environ.get("CHECKPOINT_DIR", tempfile.gettempdir())) / "aiapp_lesson17_trajectory.json"

TOOLS = [
    ToolSpec("lookup_order", "Look up an order.", {"type": "object", "properties": {"order_id": {"type": "string"}}}),
    ToolSpec("send_email", "Email the customer.", {"type": "object", "properties": {"to": {"type": "string"}}}),
]


# %% run_agent_into_thread
async def run(model: FakeAdapter) -> Thread:
    thread = Thread()
    thread.append("user_message", content="Where is order o_1?")
    for _ in range(6):
        reply = await model.complete(thread.to_messages(), tools=TOOLS)
        thread.append("assistant_message", content=reply.content, tool_calls=tool_calls_as_data(reply.tool_calls))
        if not reply.wants_tool:
            thread.append("run_finished", answer=reply.content)
            return thread
        for call in reply.tool_calls:
            thread.append("tool_result", tool_call_id=call.id, content=f"ok:{call.name}")
    return thread


def build_script() -> list[ModelResponse]:
    steps = [tool_call_response("lookup_order", {"order_id": "o_1"})]
    if INJECT_DETOUR:
        steps.append(tool_call_response("send_email", {"to": "customer@example.com"}))  # nobody asked for an email
    return steps + [ModelResponse(content="Order o_1 has shipped.")]


# %% trajectory_assertions
def tool_calls_of(thread: Thread) -> list[tuple[str, str]]:
    return [(c["name"], json.dumps(c["arguments"], sort_keys=True))
            for e in thread.events if e.type == "assistant_message" for c in e.data.get("tool_calls", [])]


def check_trajectory(thread: Thread, *, required: set[str], allowed: set[str], max_steps: int) -> list[str]:
    calls = tool_calls_of(thread)
    names = [n for n, _ in calls]
    failures = []
    if not required <= set(names):
        failures.append(f"missing required tools: {required - set(names)}")
    if extra := set(names) - allowed:
        failures.append(f"unnecessary or forbidden tools: {extra}")
    if len(calls) != len(set(calls)):
        failures.append("same call repeated")
    if thread.steps() > max_steps:
        failures.append(f"too many steps: {thread.steps()} > {max_steps}")
    final = next((e.data["answer"] for e in thread.events if e.type == "run_finished"), "")
    if "shipped" not in final:
        failures.append("final answer wrong")
    return failures


# %% record_and_replay
async def main() -> None:
    thread = await run(FakeAdapter(script=build_script()))
    failures = check_trajectory(thread, required={"lookup_order"}, allowed={"lookup_order"}, max_steps=3)
    print(f"live run: tools={[n for n, _ in tool_calls_of(thread)]} -> {'PASS' if not failures else 'FAIL ' + '; '.join(failures)}")
    if not failures:
        FIXTURE.write_text(thread.to_json(), encoding="utf-8")
        print(f"recorded fixture: {FIXTURE}")
    if FIXTURE.exists():
        replayed = Thread.load(FIXTURE)
        again = check_trajectory(replayed, required={"lookup_order"}, allowed={"lookup_order"}, max_steps=3)
        print(f"replay from fixture (no model involved): {'PASS' if not again else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(main())
