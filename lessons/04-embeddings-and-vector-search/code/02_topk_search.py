"""Vector search is: embed everything, embed the query, take the k nearest.

Brute force compares the query with every stored vector. It is exact and
fine up to a few hundred thousand rows; beyond that you trade exactness for
speed with an approximate index (HNSW, IVFFlat), which is what pgvector and
every vector database give you.

Run:  uv run python lessons/04-embeddings-and-vector-search/code/02_topk_search.py
      K=1 uv run python lessons/04-embeddings-and-vector-search/code/02_topk_search.py
Expect: top-k results with scores for two queries, plus the number of
        comparisons made, to make the O(N) cost concrete.
"""

# %% imports
import heapq
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

toy = import_module("01_toy_embeddings_and_cosine")

K = int(os.environ.get("K", "3"))

DOCS = {
    "doc_1": "Reset your password from the account settings page.",
    "doc_2": "Two-factor authentication can be enabled under security.",
    "doc_3": "Refunds are processed within five business days.",
    "doc_4": "To change your email address, verify the new one first.",
    "doc_5": "Contact support if your account is locked after failed logins.",
    "doc_6": "Shipping is free for orders over fifty dollars.",
}


# %% index
class VectorIndex:
    def __init__(self) -> None:
        self._rows: dict[str, list[float]] = {}
        self.comparisons = 0

    def add(self, doc_id: str, text: str) -> None:
        self._rows[doc_id] = toy.embed(text)

    def search(self, query: str, k: int) -> list[tuple[float, str]]:
        q = toy.embed(query)
        scored = []
        for doc_id, vec in self._rows.items():
            self.comparisons += 1
            scored.append((toy.cosine(q, vec), doc_id))
        return heapq.nlargest(k, scored)


# %% run
def main() -> None:
    index = VectorIndex()
    for doc_id, text in DOCS.items():
        index.add(doc_id, text)
    for query in ["password reset", "my account got locked"]:
        print(f"query: {query!r}")
        for score, doc_id in index.search(query, K):
            print(f"  {score:5.3f} {doc_id}: {DOCS[doc_id]}")
    print(f"\n{index.comparisons} vector comparisons for 2 queries over {len(DOCS)} docs.")
    print("brute force is O(N) per query. at 10 million rows you need an approximate index; see the README for pgvector.")


if __name__ == "__main__":
    main()
