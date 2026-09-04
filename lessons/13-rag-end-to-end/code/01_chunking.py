"""Step two of seven: chunking. The chunk is the unit of retrieval, so its size decides what can be found.

Paragraph-aware chunks with one paragraph of overlap. Too large and every
chunk matches every query weakly; too small and the answer is split across
chunks that no longer contain the question's words together.

Run:  uv run python lessons/13-rag-end-to-end/code/01_chunking.py
      CHUNK_SIZE=5000 uv run python lessons/13-rag-end-to-end/code/01_chunking.py   # one chunk per document
      CHUNK_SIZE=80 uv run python lessons/13-rag-end-to-end/code/01_chunking.py     # sentences torn apart
Expect: chunk count, size distribution, and whether each golden answer phrase still lives inside a single chunk.
"""

# %% imports
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ragkit import load_corpus  # noqa: E402

CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "450"))
GOLDEN = json.loads((Path(__file__).parent / "golden.json").read_text(encoding="utf-8"))


# %% inspect
def main() -> None:
    chunks = load_corpus(max_chars=CHUNK_SIZE)
    sizes = sorted(len(c.text) for c in chunks)
    print(f"max_chars={CHUNK_SIZE}: {len(chunks)} chunks, sizes min={sizes[0]} median={sizes[len(sizes)//2]} max={sizes[-1]}")
    for c in chunks[:3]:
        print(f"  {c.id:18} {len(c.text):4} chars  {c.text[:60]!r}...")
    intact = sum(1 for g in GOLDEN if any(g["must_contain"] in c.text for c in chunks))
    print(f"golden phrases still inside one chunk: {intact}/{len(GOLDEN)}")
    if CHUNK_SIZE > 2000:
        print("note: whole documents as chunks. Findable, but the model gets 4x the tokens it needs and BM25 scores flatten.")
    if CHUNK_SIZE < 150:
        print("note: paragraphs exceed max_chars, so each paragraph becomes its own chunk anyway; below sentence level you would start losing phrases.")


if __name__ == "__main__":
    main()
