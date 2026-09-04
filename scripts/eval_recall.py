"""Recall@k over the M4 golden set, with every miss classified.

Run:  uv run python scripts/eval_recall.py                      # in-memory store, hashing embedding
      uv run python scripts/eval_recall.py --k 3 --max-chars 300
      DATABASE_URL=... uv run python scripts/eval_recall.py --postgres --tenant tenant-demo
      EMBEDDING_PROVIDER=dashscope uv run python scripts/eval_recall.py   # real embedding model

Recall@k = share of questions whose `must_contain` phrase appears in a top-k chunk.
Misses are classified: `not_indexed` (the phrase is in no chunk at all: a chunking
problem), `outside_top_k` (indexed but ranked too low: a retrieval problem).
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

from aiapp.adapters.embeddings import get_embedding_adapter
from aiapp.knowledge import Retriever, chunk_document, parse_markdown
from aiapp.knowledge.memory_store import InMemoryKnowledgeStore

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "project/m4-rag-and-memory/docs-sample"
GOLDEN = ROOT / "project/m4-rag-and-memory/golden/qa.jsonl"


def load_golden() -> list[dict]:
    return [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]


async def run(k: int, max_chars: int, tenant: str, postgres: bool, retrievers: list[str]) -> dict:
    embedder = get_embedding_adapter()
    if postgres:
        from aiapp.knowledge.postgres_store import PostgresKnowledgeStore

        store = PostgresKnowledgeStore.from_url(os.environ["DATABASE_URL"])
    else:
        store = InMemoryKnowledgeStore()
    retriever = Retriever(store, embedder, max_chars=max_chars)
    for path in sorted(DOCS.glob("*.md")):
        await retriever.ingest(tenant, parse_markdown(path.stem, path.read_text(encoding="utf-8")))

    golden = load_golden()
    all_text = " ".join(  # what the chunker produced, independent of the store: decides "not_indexed" vs "outside_top_k"
        c.text for path in sorted(DOCS.glob("*.md")) for c in chunk_document(parse_markdown(path.stem, path.read_text(encoding="utf-8")), max_chars=max_chars)
    )
    results: dict[str, dict] = {}
    for name in retrievers:
        hits_at = {kk: 0 for kk in (1, 3, k)}
        misses = []
        for g in golden:
            if name == "hybrid":
                ranked = await retriever.search(g["q"], tenant_id=tenant, k=k)
            elif name == "vector":
                qvec = (await embedder.embed([g["q"]]))[0]
                ranked = await store.search_vector(tenant, qvec, k=k, embedding_model=embedder.name)
            else:
                ranked = await store.search_text(tenant, g["q"], k=k)
            for kk in hits_at:
                if any(g["must_contain"] in h.text for h in ranked[:kk]):
                    hits_at[kk] += 1
            if not any(g["must_contain"] in h.text for h in ranked[:k]):
                indexed = g["must_contain"] in all_text
                misses.append({"q": g["q"], "class": "outside_top_k" if indexed else "not_indexed", "top": [h.citation_id for h in ranked[:3]]})
        n = len(golden)
        results[name] = {f"recall@{kk}": round(v / n, 3) for kk, v in hits_at.items()} | {"misses": misses}
    if hasattr(store, "dispose"):
        await store.dispose()
    return {"embedding": embedder.name, "max_chars": max_chars, "k": k, "questions": len(golden), "retrievers": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--max-chars", type=int, default=600)
    parser.add_argument("--tenant", default="eval-tenant")
    parser.add_argument("--postgres", action="store_true")
    parser.add_argument("--json", action="store_true", help="print the raw report")
    args = parser.parse_args()
    report = asyncio.run(run(args.k, args.max_chars, args.tenant, args.postgres, ["text", "vector", "hybrid"]))
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return
    print(f"embedding={report['embedding']} max_chars={report['max_chars']} questions={report['questions']}")
    print(f"{'retriever':10} {'R@1':>6} {'R@3':>6} {'R@' + str(args.k):>6}  misses")
    for name, r in report["retrievers"].items():
        print(f"{name:10} {r['recall@1']:6.2f} {r['recall@3']:6.2f} {r[f'recall@{args.k}']:6.2f}  {len(r['misses'])}")
    for name, r in report["retrievers"].items():
        for m in r["misses"]:
            print(f"  [{name}] {m['class']:14} {m['q']!r} -> {m['top']}")


if __name__ == "__main__":
    main()
