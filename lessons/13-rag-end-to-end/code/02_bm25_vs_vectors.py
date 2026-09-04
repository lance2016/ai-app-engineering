"""Step four of seven, first half: two retrievers that fail differently.

BM25 finds exact words and misses paraphrases. The toy vector retriever
(hashed bag of words, same as lesson 04) is a stand-in for a real embedding
model: it also matches words here, but a real one matches meaning. Neither
is enough on its own, which is why step four is "hybrid".

Run:  uv run python lessons/13-rag-end-to-end/code/02_bm25_vs_vectors.py
Expect: for three queries, the top-3 chunks from each retriever side by side.
"""

# %% imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ragkit import BM25, embed, load_corpus, vector_rank  # noqa: E402

QUERIES = [
    "How fast is express delivery?",             # exact words present: both do fine
    "money back for a used digital download",   # paraphrase of "refund ... download link has been used"
    "water damage warranty",                    # "water" vs "liquid": lexical miss
]


# %% compare
def main() -> None:
    chunks = load_corpus(max_chars=450)
    bm25 = BM25(chunks)
    vectors = [embed(c.text) for c in chunks]
    for q in QUERIES:
        print(f"\nQ: {q}")
        lex = bm25.rank(q)[:3]
        vec = vector_rank(q, vectors)[:3]
        print(f"  bm25   -> {[chunks[i].id for i in lex]}  top score {bm25.score(q, lex[0]):.2f}")
        print(f"  vector -> {[chunks[i].id for i in vec]}")
    print("\nA real embedding model would place 'water' near 'liquid' and 'money back' near 'refund'. The toy one cannot; that gap is exactly what you pay an embedding API for.")


if __name__ == "__main__":
    main()
