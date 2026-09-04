"""Step four, second half, and step five: fuse two rankings, then rerank the top of the fused list.

Reciprocal rank fusion needs no score calibration between retrievers, which
is why it is the default way to combine BM25 and vectors. Reranking then
spends more compute on fewer candidates. Here the reranker is a phrase-overlap
heuristic standing in for a cross-encoder; the shape of the pipeline is the point.

Run:  uv run python lessons/13-rag-end-to-end/code/03_hybrid_and_rerank.py
Expect: bm25, vector, fused and reranked top-3 for a query, with the fused list
        recovering a hit that one retriever alone ranked low.
"""

# %% imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ragkit import BM25, Chunk, embed, load_corpus, rrf, tokenize, vector_rank  # noqa: E402


# %% rerank
def rerank(query: str, candidates: list[Chunk], top_n: int = 3) -> list[Chunk]:
    """Stand-in for a cross-encoder: reward chunks that contain query bigrams, not just unigrams."""
    q = tokenize(query)
    bigrams = {(a, b) for a, b in zip(q, q[1:])}

    def score(c: Chunk) -> float:
        t = tokenize(c.text)
        hits = sum(1 for a, b in zip(t, t[1:]) if (a, b) in bigrams)
        return hits + 0.01 * sum(1 for w in q if w in t)

    return sorted(candidates, key=score, reverse=True)[:top_n]


# %% run
def main() -> None:
    chunks = load_corpus(max_chars=450)
    bm25, vectors = BM25(chunks), [embed(c.text) for c in chunks]
    query = "same day dispatch cutoff time for orders"
    lex, vec = bm25.rank(query), vector_rank(query, vectors)
    fused = rrf(lex, vec)
    ids = lambda ranking, n=3: [chunks[i].id for i in ranking[:n]]
    print(f"Q: {query}")
    print(f"  bm25    {ids(lex)}")
    print(f"  vector  {ids(vec)}")
    print(f"  rrf     {ids(fused)}")
    top = rerank(query, [chunks[i] for i in fused[:8]])
    print(f"  rerank  {[c.id for c in top]}")
    print(f"\ntop chunk after rerank:\n  {top[0].text[:160]!r}")


if __name__ == "__main__":
    main()
