"""Handoff: one agent transfers the conversation to another. How much history travels with it?

The triage agent calls transfer_to_billing as a tool. The runtime switches the
active agent and decides what the specialist sees: the full history, a summary,
or only the last user message. Each policy changes the specialist's behaviour
and its token bill. The choice belongs to the runtime, not to either agent.

Run:  uv run python lessons/10-multi-agent-handoff/code/01_handoff.py                 # HANDOFF_HISTORY=full
      HANDOFF_HISTORY=summary uv run python lessons/10-multi-agent-handoff/code/01_handoff.py
      HANDOFF_HISTORY=last    uv run python lessons/10-multi-agent-handoff/code/01_handoff.py
Expect: the messages the billing agent receives, printed per policy.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response

POLICY = os.environ.get("HANDOFF_HISTORY", "full")
TRANSFER = ToolSpec("transfer_to_billing", "Hand the conversation to the billing specialist.", {"type": "object", "properties": {"reason": {"type": "string"}}})


# %% agents
@dataclass
class Agent:
    name: str
    instructions: str
    model: FakeAdapter
    tools: list[ToolSpec]


def context_for_specialist(history: list[Message], reason: str) -> list[Message]:
    """The runtime's handoff filter. This is where the policy lives."""
    if POLICY == "full":
        return history
    if POLICY == "last":
        return [m for m in history if m.role == "user"][-1:]
    if POLICY == "summary":
        summary = f"Triage handed off. Reason: {reason}. User turns so far: {sum(1 for m in history if m.role == 'user')}."
        return [Message(role="user", content=summary), *[m for m in history if m.role == "user"][-1:]]
    raise SystemExit(f"unknown HANDOFF_HISTORY {POLICY!r}")


# %% run
async def main() -> None:
    triage = Agent("triage", "Classify and route.", FakeAdapter(script=[tool_call_response("transfer_to_billing", {"reason": "duplicate charge"})]), [TRANSFER])
    billing = Agent("billing", "Resolve billing issues. Ask for the order id if missing.", FakeAdapter(script=[ModelResponse(content="I see the duplicate charge concern. Could you share the order id?")]), [])

    history = [
        Message(role="user", content="Hi, I bought a kettle last week."),
        Message(role="assistant", content="Welcome! How can I help with it?"),
        Message(role="user", content="I was charged twice for it."),
    ]
    reply = await triage.model.complete([Message(role="system", content=triage.instructions), *history], tools=triage.tools)
    call = reply.tool_calls[0]
    print(f"{triage.name} -> {call.name}({call.arguments})")

    specialist_view = context_for_specialist(history, call.arguments["reason"])
    print(f"\npolicy={POLICY}: billing agent receives {len(specialist_view)} message(s):")
    for m in specialist_view:
        print(f"  {m.role:10} {m.content}")
    answer = await billing.model.complete([Message(role="system", content=billing.instructions), *specialist_view], tools=billing.tools)
    print(f"\n{billing.name}: {answer.content}")


if __name__ == "__main__":
    asyncio.run(main())
