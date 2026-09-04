"""One thread, many agents: the runtime owns the state; agents get scoped views and can fail safely.

Every agent's turn is recorded in the same thread with an `agent` tag. A
specialist that raises does not take the run down: the runtime records the
failure as an event and returns control to the triage agent, which can answer
with what it has. Nothing about this is visible to the models beyond the
messages the runtime chooses to show them.

Run:  uv run python lessons/10-multi-agent-handoff/code/03_ownership_and_fallback.py
      INJECT_SPECIALIST_FAIL=1 uv run python lessons/10-multi-agent-handoff/code/03_ownership_and_fallback.py
Expect: triage -> billing -> answer. With injection billing raises; the thread
        shows a handoff_failed event and triage gives a fallback reply.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, Message, ModelResponse, Thread

INJECT_SPECIALIST_FAIL = os.environ.get("INJECT_SPECIALIST_FAIL") == "1"


# %% scoped_view
def view_for(thread: Thread, agent: str) -> list[Message]:
    """User turns are shared; assistant turns are only shown to the agent that produced them."""
    out: list[Message] = []
    for e in thread.events:
        if e.type == "user_message":
            out.append(Message(role="user", content=e.data["content"]))
        elif e.type == "assistant_message" and e.data.get("agent") == agent:
            out.append(Message(role="assistant", content=e.data["content"]))
    return out


# %% agents
async def run_billing(thread: Thread) -> str:
    if INJECT_SPECIALIST_FAIL:
        raise RuntimeError("billing backend unavailable")
    model = FakeAdapter(script=[ModelResponse(content="Refund for order o_77 issued; expect it in 3-5 days.")])
    reply = await model.complete(view_for(thread, "billing"))
    thread.append("assistant_message", agent="billing", content=reply.content)
    return reply.content


async def run_triage(thread: Thread, *, fallback_note: str | None = None) -> str:
    text = "I couldn't reach billing just now; I've logged your request and someone will follow up within a day." if fallback_note else "Let me pass you to billing."
    model = FakeAdapter(script=[ModelResponse(content=text)])
    reply = await model.complete(view_for(thread, "triage"))
    thread.append("assistant_message", agent="triage", content=reply.content)
    return reply.content


# %% orchestration
async def handle(thread: Thread) -> str:
    print(f"triage: {await run_triage(thread)}")
    thread.append("handoff", source="triage", target="billing")
    try:
        answer = await run_billing(thread)
        print(f"billing: {answer}")
        return answer
    except Exception as exc:  # noqa: BLE001 - any specialist failure is handled the same way
        thread.append("handoff_failed", target="billing", error=str(exc))
        answer = await run_triage(thread, fallback_note=str(exc))
        print(f"triage (fallback): {answer}")
        return answer


# %% run
async def main() -> None:
    thread = Thread()
    thread.append("user_message", content="Please refund order o_77, it arrived broken.")
    await handle(thread)
    print("\nthread events:", [f"{e.type}{'/' + e.data['agent'] if 'agent' in e.data else ''}" for e in thread.events])
    print("billing's view had", len(view_for(thread, "billing")), "message(s); triage's view had", len(view_for(thread, "triage")))


if __name__ == "__main__":
    asyncio.run(main())
