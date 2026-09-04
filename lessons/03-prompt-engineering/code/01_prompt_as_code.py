"""A prompt is code: built from parts, rendered deterministically, versioned.

Frameworks hide prompts behind `role=` and `goal=` parameters; you then cannot
see or tune the exact tokens the model gets. Here the system prompt is a
plain function of typed inputs. You can diff it, test it and print exactly
what was sent.

Run:  uv run python lessons/03-prompt-engineering/code/01_prompt_as_code.py
      PROMPT_VERSION=v2 uv run python lessons/03-prompt-engineering/code/01_prompt_as_code.py
Expect: the fully rendered system prompt, section by section, then the
        message list as the adapter would send it.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass, field

from aiapp import FakeAdapter, Message

PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "v1")


# %% prompt_parts
@dataclass(frozen=True)
class SupportPromptInputs:
    product: str
    tone: str = "friendly and brief"
    forbidden_topics: tuple[str, ...] = ("pricing of competitors",)
    examples: tuple[tuple[str, str], ...] = field(default_factory=tuple)


def render_v1(inp: SupportPromptInputs) -> str:
    sections = [
        f"You are the support assistant for {inp.product}.",
        f"Tone: {inp.tone}.",
        "Do not discuss: " + ", ".join(inp.forbidden_topics) + ".",
        "Answer in at most three sentences.",
    ]
    return "\n".join(sections)


def render_v2(inp: SupportPromptInputs) -> str:
    """v2 adds an output contract and examples. Same inputs, different tokens."""
    sections = [
        f"# Role\nYou are the support assistant for {inp.product}.",
        f"# Style\n{inp.tone}. At most three sentences.",
        "# Never discuss\n" + "\n".join(f"- {t}" for t in inp.forbidden_topics),
        "# Output\nStart with the direct answer. If you cannot help, say so and name the right channel.",
    ]
    if inp.examples:
        shots = "\n\n".join(f"User: {q}\nAssistant: {a}" for q, a in inp.examples)
        sections.append(f"# Examples\n{shots}")
    return "\n\n".join(sections)


RENDERERS = {"v1": render_v1, "v2": render_v2}


# %% run
async def main() -> None:
    inputs = SupportPromptInputs(
        product="Nimbus Notes",
        examples=(("Can I export to PDF?", "Yes. Open the note, choose Share, then Export as PDF."),),
    )
    system = RENDERERS[PROMPT_VERSION](inputs)
    print(f"=== system prompt {PROMPT_VERSION} ({len(system)} chars) ===\n{system}\n")
    messages = [Message(role="system", content=system), Message(role="user", content="How do I share a note?")]
    reply = await FakeAdapter().complete(messages)
    print("=== messages sent ===")
    for m in messages:
        print(f"[{m.role}] {m.content[:60]}{'...' if len(m.content) > 60 else ''}")
    print(f"\nfake reply: {reply.content}")
    print("\nthe prompt version is a code path, so a change to it goes through review and tests like any other change.")


if __name__ == "__main__":
    asyncio.run(main())
