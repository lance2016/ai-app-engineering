"""Every turn, the runtime assembles the context window from parts. Nothing goes in by accident.

A ContextBuilder takes the stable instructions, retrieved documents, a running
summary, recent history and fresh tool results, lays them out in a fixed order
and enforces a token budget. The final message list is printed before the model
sees it: if you cannot show what the model received, you cannot debug it.

Run:  uv run python lessons/08-context-engineering-for-agents/code/01_context_builder.py
      INJECT_OVERFLOW=1 uv run python lessons/08-context-engineering-for-agents/code/01_context_builder.py
Expect: the assembled window with a per-section token report. With injection the
        history is too long; the builder drops the oldest turns and says which.
"""

# %% imports
import os
from dataclasses import dataclass, field

from aiapp import Message

INJECT_OVERFLOW = os.environ.get("INJECT_OVERFLOW") == "1"


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# %% builder
@dataclass
class ContextBuilder:
    """Sections in priority order. Stable things first, volatile things last."""

    system: str
    budget_tokens: int
    documents: list[str] = field(default_factory=list)
    summary: str = ""
    history: list[Message] = field(default_factory=list)
    dropped: list[Message] = field(default_factory=list)

    def build(self) -> list[Message]:
        fixed = [Message(role="system", content=self.system)]
        if self.documents:
            docs = "\n\n".join(f"<doc id={i}>\n{d}\n</doc>" for i, d in enumerate(self.documents))
            fixed.append(Message(role="user", content=f"Reference material:\n{docs}"))
        if self.summary:
            fixed.append(Message(role="user", content=f"Summary of earlier conversation:\n{self.summary}"))
        spent = sum(estimate_tokens(m.content) for m in fixed)
        if spent > self.budget_tokens:
            raise ValueError(f"fixed sections alone use {spent} tokens; budget is {self.budget_tokens}")
        # keep the most recent history that fits, dropping whole turns from the front
        kept: list[Message] = []
        for m in reversed(self.history):
            cost = estimate_tokens(m.content) + 8 * len(m.tool_calls)
            if spent + cost > self.budget_tokens:
                break
            kept.insert(0, m)
            spent += cost
        self.dropped = self.history[: len(self.history) - len(kept)]
        return fixed + kept

    def report(self, window: list[Message]) -> None:
        print(f"{'section':10} {'tokens':>6}")
        for m in window:
            label = m.role if m.role != "user" else ("reference" if m.content.startswith("Reference") else "summary" if m.content.startswith("Summary") else "user")
            print(f"{label:10} {estimate_tokens(m.content):>6}  {m.content[:50]!r}")
        print(f"total ~{sum(estimate_tokens(m.content) for m in window)} / budget {self.budget_tokens}; dropped {len(self.dropped)} old message(s)")


# %% run
def main() -> None:
    turns = 3 if not INJECT_OVERFLOW else 30
    history = []
    for i in range(turns):
        history.append(Message(role="user", content=f"Question {i}: what does clause {i} of the lease say about repairs?"))
        history.append(Message(role="assistant", content=f"Clause {i} makes the tenant responsible for minor repairs under 200 dollars."))
    builder = ContextBuilder(
        system="You are a lease assistant. Answer only from the reference material. Cite the doc id.",
        budget_tokens=400,
        documents=["Clause 7: The landlord maintains structural elements. Tenant handles repairs under $200."],
        summary="User is a tenant in a two-year lease; earlier we covered deposit and notice periods." if INJECT_OVERFLOW else "",
        history=history,
    )
    window = builder.build()
    builder.report(window)
    if builder.dropped:
        print(f"first dropped: {builder.dropped[0].content[:60]!r}")


if __name__ == "__main__":
    main()
