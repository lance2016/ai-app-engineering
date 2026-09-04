"""Compaction: summarise old turns so the window stays small, without losing the log.

The thread keeps every event forever (audit, replay). What the model sees is a
summary of older turns plus the recent ones. The summary is produced by a model
call, which means it can be wrong. Facts the runtime knows are critical are
carried verbatim instead of trusting the summary to keep them.

Run:  uv run python lessons/08-context-engineering-for-agents/code/02_compaction.py
      INJECT_LOSSY=1 uv run python lessons/08-context-engineering-for-agents/code/02_compaction.py
Expect: after compaction the model still knows the user is allergic to peanuts.
        With injection the summary drops that fact; the protected-facts list catches it.
"""

# %% imports
import os

from aiapp import FakeAdapter, Message, ModelResponse, Thread

INJECT_LOSSY = os.environ.get("INJECT_LOSSY") == "1"
COMPACT_AFTER = 6  # messages; real systems use a token threshold


# %% protected_facts
def extract_protected(thread: Thread) -> list[str]:
    """Deterministic extraction of facts too important to leave to a summary."""
    facts = []
    for e in thread.events:
        if e.type == "user_message" and "allergic" in e.data["content"].lower():
            facts.append(e.data["content"])
    return facts


# %% compaction
async def compact(thread: Thread, summarizer: FakeAdapter) -> None:
    messages = thread.to_messages()
    old, recent = messages[:-2], messages[-2:]
    transcript = "\n".join(f"{m.role}: {m.content}" for m in old)
    reply = await summarizer.complete([Message(role="user", content=f"Summarize for continuity:\n{transcript}")])
    thread.append("compaction", summary=reply.content, covers=len(old), protected=extract_protected(thread))
    print(f"compacted {len(old)} messages into {len(reply.content)} chars; protected facts: {len(extract_protected(thread))}")


def window_for_model(thread: Thread) -> list[Message]:
    """Latest compaction summary + protected facts + messages after it."""
    last = next((e for e in reversed(thread.events) if e.type == "compaction"), None)
    messages = thread.to_messages()
    if last is None:
        return messages
    head = [Message(role="user", content=f"Summary so far: {last.data['summary']}")]
    if last.data["protected"]:
        head.append(Message(role="user", content="Facts to keep verbatim: " + " | ".join(last.data["protected"])))
    return head + messages[last.data["covers"]:]


# %% run
async def main() -> None:
    thread = Thread()
    turns = [
        ("I'm planning a dinner party for six.", "Great, what cuisine are you thinking?"),
        ("Thai. Also, I'm allergic to peanuts.", "Noted, I'll avoid peanuts in every suggestion."),
        ("Budget is about 20 dollars a head.", "That works well for Thai; I'll keep it under budget."),
        ("Two guests are vegetarian.", "Understood, at least two vegetarian mains."),
    ]
    for user, assistant in turns:
        thread.append("user_message", content=user)
        thread.append("assistant_message", content=assistant)

    good = "Dinner for six, Thai food, ~$20 per head, two vegetarians, host is allergic to peanuts."
    lossy = "Dinner for six, Thai food, ~$20 per head, two vegetarians."
    summarizer = FakeAdapter(script=[ModelResponse(content=lossy if INJECT_LOSSY else good)])
    if len(thread.to_messages()) > COMPACT_AFTER:
        await compact(thread, summarizer)

    window = window_for_model(thread)
    print(f"model sees {len(window)} messages; thread keeps {len(thread.events)} events")
    for m in window:
        print(f"  {m.role:10} {m.content[:90]}")
    summary = next(e for e in reversed(thread.events) if e.type == "compaction").data["summary"].lower()
    visible = " ".join(m.content for m in window).lower()
    print("summary kept the allergy:", "peanut" in summary)
    print("allergy visible to model anyway:", "peanut" in visible, "(protected facts)")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
