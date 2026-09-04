"""Routing: classify first, then send the input to a specialised prompt or a cheaper model.

One classifier call decides the lane. Easy questions go to a small, cheap model
with a short prompt; refund disputes go to a stronger model with the policy in
its context. The classifier's output is validated against the known lanes;
an unknown label falls back to the safest lane instead of crashing.

Run:  uv run python lessons/09-workflow-vs-agent/code/02_routing.py
      INJECT_UNKNOWN_LANE=1 uv run python lessons/09-workflow-vs-agent/code/02_routing.py
Expect: each question prints its lane and the model tier used; the unknown label
        falls back to the human_review lane.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_UNKNOWN_LANE = os.environ.get("INJECT_UNKNOWN_LANE") == "1"

LANES = {
    "faq": ("cheap-model", "Answer briefly from the FAQ."),
    "refund": ("strong-model", "You handle refund disputes. Policy: refunds within 30 days, exceptions need a manager."),
    "human_review": (None, None),
}


# %% router
async def classify(classifier: FakeAdapter, question: str) -> str:
    reply = await classifier.complete([Message(role="system", content=f"Reply with one of {list(LANES)}."), Message(role="user", content=question)])
    label = reply.content.strip().lower()
    if label not in LANES:
        print(f"  classifier said {label!r}, not a known lane -> human_review")
        return "human_review"
    return label


async def route(question: str, classifier: FakeAdapter, workers: dict[str, FakeAdapter]) -> str:
    lane = await classify(classifier, question)
    tier, instruction = LANES[lane]
    if tier is None:
        return f"[{lane}] queued for a person"
    reply = await workers[lane].complete([Message(role="system", content=instruction), Message(role="user", content=question)])
    return f"[{lane} via {tier}] {reply.content}"


# %% run
async def main() -> None:
    questions = ["What are your opening hours?", "I want a refund for an order from 45 days ago."]
    labels = ["faq", "billing_dispute" if INJECT_UNKNOWN_LANE else "refund"]
    classifier = FakeAdapter(script=[ModelResponse(content=l) for l in labels])
    workers = {
        "faq": FakeAdapter(script=[ModelResponse(content="9am to 6pm, Monday to Saturday.")]),
        "refund": FakeAdapter(script=[ModelResponse(content="45 days is past the 30-day window; I'll escalate to a manager for an exception.")]),
    }
    for q in questions:
        print(f"Q: {q}\n  {await route(q, classifier, workers)}")


if __name__ == "__main__":
    asyncio.run(main())
