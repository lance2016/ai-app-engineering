"""State is a fold over an append-only event log, not a pile of variables.

The thread records what happened. The messages for the model, the run status
and the pending tool calls are all derived from it on demand. Serialise the
list and you have serialised the whole run; load it and you can continue.

Run:  uv run python lessons/07-agent-state-and-runtime/code/01_state_as_event_log.py
Expect: the same thread printed three ways (events, model messages, derived
        execution state), then round-tripped through JSON with nothing lost.
"""

# %% imports
from aiapp import Thread, ToolCall, tool_calls_as_data


# %% build_a_thread
def build_thread() -> Thread:
    """Replay a short run by hand so the event shapes are visible."""
    t = Thread(thread_id="thr_demo")
    t.append("user_message", content="Book me a table for two tonight.")
    call = ToolCall(id="c1", name="find_restaurants", arguments={"party": 2})
    t.append("assistant_message", tool_calls=tool_calls_as_data((call,)))
    t.append("tool_result", tool_call_id="c1", content='["Noodle House", "Sea Breeze"]')
    ask = ToolCall(id="c2", name="request_human_input", arguments={"question": "Noodle House or Sea Breeze?"})
    t.append("assistant_message", tool_calls=tool_calls_as_data((ask,)))
    t.append("human_input_requested", tool_call_id="c2", question="Noodle House or Sea Breeze?")
    return t


# %% derived_views
def show(t: Thread) -> None:
    print("-- events (what happened) --")
    for e in t.events:
        print(f"  {e.type:24} {e.data}")
    print("-- messages (what the model sees) --")
    for m in t.to_messages():
        summary = m.content or f"tool_calls={[c.name for c in m.tool_calls]}"
        print(f"  {m.role:10} {summary}")
    print("-- execution state (derived, never stored) --")
    print(f"  status={t.status()} steps={t.steps()} pending={[c.name for c in t.pending_tool_calls()]}")


# %% run
def main() -> None:
    t = build_thread()
    show(t)
    restored = Thread.from_json(t.to_json())
    assert restored.events == t.events and restored.status() == "paused"
    print(f"\nround-trip through JSON: {len(t.to_json())} bytes, identical")


if __name__ == "__main__":
    main()
