"""Different failures need different recovery. "Ask the model again" is not a strategy.

The runtime classifies each tool outcome and routes it: transient errors are
retried with a cap, invalid input is fed back so the model can fix it, an
off-track model (same call repeated) gets one warning then the run escalates
to a human. Each route is deterministic code; the model never decides how to
recover from its own mistakes.

Run:  uv run python lessons/06-agent-loop/code/03_failure_routing.py
      INJECT_OFF_TRACK=1 uv run python lessons/06-agent-loop/code/03_failure_routing.py
Expect: a flaky tool succeeds on the second try; with injection the model
        repeats itself, is warned once, then the run stops with needs_human.
"""

# %% imports
import asyncio
import json
import os
from enum import StrEnum

from aiapp import FakeAdapter, Message, ModelResponse, ToolCall, ToolSpec, tool_call_response

INJECT_OFF_TRACK = os.environ.get("INJECT_OFF_TRACK") == "1"


# %% taxonomy
class Failure(StrEnum):
    TRANSIENT = "transient"  # network blip, rate limit, timeout
    INVALID_INPUT = "invalid_input"  # bad arguments; the model can fix this
    OFF_TRACK = "off_track"  # same call repeated; more turns will not help


class Route(StrEnum):
    RETRY = "retry"
    FEEDBACK = "feedback"
    ESCALATE = "escalate"


ROUTES = {Failure.TRANSIENT: Route.RETRY, Failure.INVALID_INPUT: Route.FEEDBACK, Failure.OFF_TRACK: Route.ESCALATE}


class TransientError(Exception):
    pass


# %% flaky_tool
class FlakyLookup:
    """Fails the first time it is called, then works. Stands in for any network dependency."""

    def __init__(self) -> None:
        self.attempts = 0

    def __call__(self, args: dict) -> str:
        self.attempts += 1
        if self.attempts == 1:
            raise TransientError("connection reset")
        if "order_id" not in args:
            raise ValueError("order_id is required")
        return json.dumps({"order_id": args["order_id"], "status": "shipped"})


SPEC = ToolSpec("lookup_order", "Look up an order.", {"type": "object", "properties": {"order_id": {"type": "string"}}})


# %% execute_with_routing
async def execute(call: ToolCall, tool: FlakyLookup, *, max_retries: int = 2) -> Message:
    for attempt in range(1, max_retries + 2):
        try:
            return Message(role="tool", tool_call_id=call.id, content=tool(call.arguments))
        except TransientError as exc:
            print(f"  {Failure.TRANSIENT} -> {Route.RETRY} (attempt {attempt}): {exc}")
            await asyncio.sleep(0.05 * attempt)
        except ValueError as exc:
            print(f"  {Failure.INVALID_INPUT} -> {Route.FEEDBACK}: {exc}")
            return Message(role="tool", tool_call_id=call.id, is_error=True, content=str(exc))
    return Message(role="tool", tool_call_id=call.id, is_error=True, content="tool unavailable after retries")


def signature(call: ToolCall) -> str:
    return f"{call.name}:{json.dumps(call.arguments, sort_keys=True)}"


# %% run_agent
async def run_agent(model: FakeAdapter, goal: str, tool: FlakyLookup) -> str:
    messages = [Message(role="user", content=goal)]
    seen: set[str] = set()
    warned = False
    for _ in range(8):
        reply = await model.complete(messages, tools=[SPEC])
        if not reply.wants_tool:
            return f"finished: {reply.content}"
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            sig = signature(call)
            if sig in seen:
                if warned:
                    print(f"  {Failure.OFF_TRACK} -> {Route.ESCALATE}: repeated {call.name} after a warning")
                    return "needs_human: the model is looping; a person should look at this run"
                warned = True
                print(f"  {Failure.OFF_TRACK} -> {Route.FEEDBACK} (one warning)")
                messages.append(Message(role="tool", tool_call_id=call.id, is_error=True, content="you already called this with the same arguments; use the previous result or try something else"))
                continue
            seen.add(sig)
            messages.append(await execute(call, tool))
    return "step_limit"


# %% script
def build_script() -> list[ModelResponse]:
    call = tool_call_response("lookup_order", {"order_id": "o_1"}, call_id="c1")
    if INJECT_OFF_TRACK:
        return [call, call, call, ModelResponse(content="unreachable")]
    return [call, ModelResponse(content="Order o_1 has shipped.")]


# %% run
async def main() -> None:
    outcome = await run_agent(FakeAdapter(script=build_script()), "Where is order o_1?", FlakyLookup())
    print(outcome)


if __name__ == "__main__":
    asyncio.run(main())
