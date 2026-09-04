"""Side effects the user did not explicitly ask for go through a confirmation gate.

The runtime does not execute a side-effecting tool on the model's word alone.
It pauses, asks the user, and only continues on an explicit yes. Declining is
reported back to the model as a normal tool result so it can respond
gracefully instead of pretending the action happened.

Run:  uv run python lessons/05-tool-calling/code/04_confirmation_gate.py
      USER_DECISION=no uv run python lessons/05-tool-calling/code/04_confirmation_gate.py
Expect: with yes, the deletion runs after the gate. With no, nothing is deleted
        and the model is told so.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass

from aiapp import FakeAdapter, Message, ModelResponse, ToolCall, ToolSpec, tool_call_response

USER_DECISION = os.environ.get("USER_DECISION", "yes")

SIDE_EFFECTING = frozenset({"delete_doc"})
DELETE_SPEC = ToolSpec("delete_doc", "Delete a document by id.", {"type": "object", "properties": {"doc_id": {"type": "string"}}})


# %% Store
@dataclass
class Store:
    docs: set[str]

    def delete(self, doc_id: str) -> str:
        self.docs.discard(doc_id)
        return f"deleted {doc_id}"


# %% ask_user
async def ask_user(call: ToolCall) -> bool:
    """Stand-in for a UI prompt. Lesson 07 turns this into pause/resume across requests."""
    print(f"confirm? {call.name}({call.arguments}) -> user says {USER_DECISION!r}")
    return USER_DECISION == "yes"


# %% run_tool
async def run_tool(store: Store, call: ToolCall) -> Message:
    if call.name in SIDE_EFFECTING and not await ask_user(call):
        return Message(role="tool", tool_call_id=call.id, is_error=True, content="user declined; nothing was changed")
    return Message(role="tool", tool_call_id=call.id, content=store.delete(call.arguments["doc_id"]))


# %% main
async def main() -> None:
    store = Store(docs={"doc_1", "doc_2"})
    final_text = "Done, doc_1 is gone." if USER_DECISION == "yes" else "Okay, I left doc_1 in place."
    model = FakeAdapter(script=[tool_call_response("delete_doc", {"doc_id": "doc_1"}), ModelResponse(content=final_text)])
    messages = [Message(role="user", content="Clean up the old draft.")]
    for _ in range(3):
        reply = await model.complete(messages, tools=[DELETE_SPEC])
        if not reply.wants_tool:
            print(f"assistant: {reply.content}")
            break
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            result = await run_tool(store, call)
            print(f"tool {call.name} -> [{'ERROR' if result.is_error else 'ok'}] {result.content}")
            messages.append(result)
    print(f"docs left: {sorted(store.docs)}")


# %% run
if __name__ == "__main__":
    asyncio.run(main())
