"""Parallelization: independent sub-tasks at once (sectioning) or several attempts at once (voting).

Sectioning: review one document for three separate concerns in parallel and
concatenate. Voting: ask three times whether an input is safe and take the
majority. Both are asyncio.gather plus a deterministic aggregator; the model
never sees the other branches.

Run:  uv run python lessons/09-workflow-vs-agent/code/03_parallelization.py
Expect: three section reviews merged, then a 2-of-3 vote result.
"""

# %% imports
import asyncio
from collections import Counter

from aiapp import FakeAdapter, Message, ModelResponse


# %% sectioning
async def review(concern: str, text: str, model: FakeAdapter) -> tuple[str, str]:
    reply = await model.complete([Message(role="system", content=f"Review only for {concern}."), Message(role="user", content=text)])
    return concern, reply.content


async def sectioned_review(text: str) -> dict[str, str]:
    concerns = {
        "security": FakeAdapter(script=[ModelResponse(content="No secrets in code; input validation missing on /upload.")]),
        "performance": FakeAdapter(script=[ModelResponse(content="N+1 query in list_orders.")]),
        "style": FakeAdapter(script=[ModelResponse(content="Consistent; two functions exceed 50 lines.")]),
    }
    results = await asyncio.gather(*(review(c, text, m) for c, m in concerns.items()))
    return dict(results)


# %% voting
async def vote_is_safe(text: str, attempts: int = 3) -> tuple[bool, Counter]:
    voters = [FakeAdapter(script=[ModelResponse(content=v)]) for v in ("safe", "unsafe", "safe")]
    replies = await asyncio.gather(*(v.complete([Message(role="user", content=f"Is this safe? {text}")]) for v in voters))
    tally = Counter(r.content.strip().lower() for r in replies)
    return tally["safe"] > attempts // 2, tally


# %% run
async def main() -> None:
    merged = await sectioned_review("def list_orders(): ...")
    for concern, finding in merged.items():
        print(f"{concern:12} {finding}")
    safe, tally = await vote_is_safe("Please summarise this contract.")
    print(f"\nvote: {dict(tally)} -> safe={safe}")


if __name__ == "__main__":
    asyncio.run(main())
