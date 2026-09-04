"""Prompt chaining: fixed steps, each model call does one easy thing, code checks in between.

Outline -> gate -> draft -> gate -> polish. The gates are deterministic: if the
outline has fewer than three sections we stop, we never let a bad intermediate
result flow downstream. Latency goes up, accuracy per step goes up more.

Run:  uv run python lessons/09-workflow-vs-agent/code/01_prompt_chaining.py
      INJECT_BAD_OUTLINE=1 uv run python lessons/09-workflow-vs-agent/code/01_prompt_chaining.py
Expect: three steps and a final text; with injection the first gate rejects the outline.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_BAD_OUTLINE = os.environ.get("INJECT_BAD_OUTLINE") == "1"


# %% steps
async def step(model: FakeAdapter, instruction: str, payload: str) -> str:
    reply = await model.complete([Message(role="system", content=instruction), Message(role="user", content=payload)])
    return reply.content


def gate_outline(outline: str) -> None:
    sections = [line for line in outline.splitlines() if line.strip()]
    if len(sections) < 3:
        raise ValueError(f"outline has {len(sections)} section(s); need at least 3")


# %% chain
async def write_article(model: FakeAdapter, topic: str) -> str:
    outline = await step(model, "Produce a 3-5 line outline.", topic)
    gate_outline(outline)  # deterministic check between steps
    print(f"outline ok ({len(outline.splitlines())} sections)")
    draft = await step(model, "Write one paragraph per outline line.", outline)
    if len(draft) < 40:
        raise ValueError("draft too short")
    print(f"draft ok ({len(draft)} chars)")
    return await step(model, "Tighten the prose; keep every fact.", draft)


# %% run
async def main() -> None:
    outline = "1. Why caching\n" if INJECT_BAD_OUTLINE else "1. Why caching\n2. Prefix caching\n3. Pitfalls"
    model = FakeAdapter(script=[
        ModelResponse(content=outline),
        ModelResponse(content="Caching saves money. Prefix caching reuses the stable part of the prompt. Pitfalls include volatile prefixes."),
        ModelResponse(content="Caching saves money; prefix caching reuses the stable prompt head; volatile prefixes defeat it."),
    ])
    try:
        print("final:", await write_article(model, "prompt caching for agents"))
    except ValueError as exc:
        print(f"chain stopped at a gate: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
