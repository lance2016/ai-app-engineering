"""Measure before you tune: Recall@k over a golden set, per retriever, per chunk size.

Each golden question names the phrase that must appear in a retrieved chunk.
Recall@k is the share of questions whose phrase shows up in the top k. Run it
for BM25, vectors and hybrid, then change CHUNK_SIZE and watch which stage
broke. Without this table every RAG change is a guess.

Run:  uv run python lessons/13-rag-end-to-end/code/05_recall_at_k.py
      CHUNK_SIZE=5000 uv run python lessons/13-rag-end-to-end/code/05_recall_at_k.py
      CHUNK_SIZE=120 uv run python lessons/13-rag-end-to-end/code/05_recall_at_k.py
Expect: a small table; the misses are listed so you can classify them.
"""

# %% imports
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ragkit import BM25, embed, load_corpus, rrf, vector_rank  # noqa: E402

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "450"))
GOLDEN = json.loads((Path(__file__).parent / "golden.json").read_text(encoding="utf-8"))


# %% evaluate
def main() -> None:
    chunks = load_corpus(max_chars=CHUNK_SIZE)
    bm25, vectors = BM25(chunks), [embed(c.text) for c in chunks]
    retrievers = {
        "bm25": lambda q: bm25.rank(q),
        "vector": lambda q: vector_rank(q, vectors),
        "hybrid": lambda q: rrf(bm25.rank(q), vector_rank(q, vectors)),
    }
    print(f"chunks={len(chunks)} (max_chars={CHUNK_SIZE})\n{'retriever':10} {'R@1':>5} {'R@3':>5} {'R@5':>5}")
    misses: dict[str, list[str]] = {}
    for name, fn in retrievers.items():
        hits = {k: 0 for k in (1, 3, 5)}
        for g in GOLDEN:
            ranked = fn(g["q"])
            for k in hits:
                if any(g["must_contain"] in chunks[i].text for i in ranked[:k]):
                    hits[k] += 1
            if not any(g["must_contain"] in chunks[i].text for i in ranked[:3]):
                misses.setdefault(name, []).append(g["q"])
        n = len(GOLDEN)
        print(f"{name:10} {hits[1]/n:5.2f} {hits[3]/n:5.2f} {hits[5]/n:5.2f}")
    for name, qs in misses.items():
        print(f"\n{name} misses @3:")
        for q in qs:
            print(f"  - {q}")


if __name__ == "__main__":
    main()
