"""Steps six and seven: generate an answer that cites chunk ids, then *verify* the citations.

The model is told to cite [chunk_id]. The runtime checks that every cited id
was actually retrieved and that the cited chunk supports the sentence. A
citation the model made up is the RAG equivalent of a hallucinated tool
call (lesson 05): it looks right and must be caught by code.

Run:  uv run python lessons/13-rag-end-to-end/code/04_generate_with_citations.py
      INJECT_FAKE_CITATION=1 uv run python lessons/13-rag-end-to-end/code/04_generate_with_citations.py
Expect: an answer with verified citations; with injection one citation points at a
        chunk that was never retrieved and is flagged.
"""

# %% imports
import asyncio
import os
import re
import sys
from pathlib import Path

from aiapp import FakeAdapter, Message, ModelResponse

sys.path.insert(0, str(Path(__file__).parent))
from ragkit import BM25, Chunk, embed, load_corpus, rrf, tokenize, vector_rank  # noqa: E402

INJECT_FAKE_CITATION = os.environ.get("INJECT_FAKE_CITATION") == "1"
CITATION = re.compile(r"\[([a-z-]+#\d+)\]")


# %% build_context
def build_context(query: str, chunks: list[Chunk], k: int = 3) -> list[Chunk]:
    bm25, vectors = BM25(chunks), [embed(c.text) for c in chunks]
    fused = rrf(bm25.rank(query), vector_rank(query, vectors))
    return [chunks[i] for i in fused[:k]]


def prompt(query: str, ctx: list[Chunk]) -> list[Message]:
    blocks = "\n\n".join(f"[{c.id}]\n{c.text}" for c in ctx)
    system = "Answer only from the sources below. After each sentence cite the source id in square brackets. If the sources do not contain the answer, say so."
    return [Message(role="system", content=f"{system}\n\nSources:\n{blocks}"), Message(role="user", content=query)]


# %% verify
def verify(answer: str, ctx: list[Chunk]) -> list[str]:
    """Return problems. Cited id must be in ctx and share words with the sentence it supports."""
    by_id = {c.id: c for c in ctx}
    problems = []
    for sentence in re.split(r"(?<=[.!?])\s+", answer):
        for cid in CITATION.findall(sentence):
            if cid not in by_id:
                problems.append(f"[{cid}] was never retrieved")
                continue
            words = set(tokenize(CITATION.sub("", sentence))) - {"the", "a", "is", "are", "to", "of", "and", "for"}
            if len(words & set(tokenize(by_id[cid].text))) < 2:
                problems.append(f"[{cid}] does not support: {sentence.strip()!r}")
    if not CITATION.search(answer):
        problems.append("no citations at all")
    return problems


# %% run
async def main() -> None:
    chunks = load_corpus(max_chars=450)
    query = "Can I return an unopened item after two weeks?"
    ctx = build_context(query, chunks)
    print(f"retrieved: {[c.id for c in ctx]}")
    good = "Unopened items can be refunded within 14 days of delivery [refund-policy#0]. Two weeks is exactly the limit, so a request on day 14 is still in time [refund-policy#0]."
    bad = "Unopened items can be refunded within 14 days of delivery [refund-policy#0]. Refunds are processed within 24 hours [shipping#3]."
    model = FakeAdapter(script=[ModelResponse(content=bad if INJECT_FAKE_CITATION else good)])
    reply = await model.complete(prompt(query, ctx))
    print(f"answer: {reply.content}")
    problems = verify(reply.content, ctx)
    print("citations verified" if not problems else "citation problems: " + "; ".join(problems))


if __name__ == "__main__":
    asyncio.run(main())
