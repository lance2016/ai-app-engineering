"""The same document, chunked two ways, answers the same query differently.

Embeddings summarise whatever text you hand them. A chunk that mixes three
topics has a vector that matches none of them well. Chunk size is therefore a
retrieval parameter, not a storage detail. This is a preview of lesson 13.

Run:  uv run python lessons/04-embeddings-and-vector-search/code/03_chunking_changes_recall.py
Expect: with one big chunk the target sentence is diluted and ranks lower;
        with sentence-level chunks it ranks first.
"""

# %% imports
import re
import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
toy = import_module("01_toy_embeddings_and_cosine")

DOCUMENT = (
    "Our return policy allows refunds within thirty days. "
    "Shipping is free for orders above fifty dollars. "
    "Gift cards never expire and can be used online or in store. "
    "To reset your password use the link on the login page. "
    "Loyalty points are earned on every purchase."
)
DISTRACTOR = "Password managers help you keep unique passwords for every site."
QUERY = "how to reset password"


# %% chunkers
def one_chunk(text: str) -> list[str]:
    return [text]


def by_sentence(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=\.)\s+", text) if s.strip()]


# %% run
def rank(chunks: list[str]) -> list[tuple[float, str]]:
    q = toy.embed(QUERY)
    return sorted(((toy.cosine(q, toy.embed(c)), c) for c in chunks), reverse=True)


def main() -> None:
    for label, chunker in [("one big chunk", one_chunk), ("sentence chunks", by_sentence)]:
        chunks = chunker(DOCUMENT) + [DISTRACTOR]
        print(f"== {label}: {len(chunks)} chunks ==")
        for score, chunk in rank(chunks)[:2]:
            print(f"  {score:5.3f} {chunk[:70]}{'...' if len(chunk) > 70 else ''}")
    print("\nthe big chunk *contains* the answer but its vector is an average of five topics,")
    print("so a distractor that is purely about passwords beats it. chunking is a retrieval decision.")


if __name__ == "__main__":
    main()
