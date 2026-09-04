"""Deleting a source must delete everything derived from it. Prove it with a drill.

A document produces chunks, embeddings, cache entries and sometimes memories.
"Right to erasure" means all of them go. The only way to know your pipeline
does this is to run the deletion and then search for residue. With the
injection on, one derived store is skipped and the drill catches it.

Run:  uv run python lessons/15-data-engineering/code/03_delete_drill.py
      INJECT_ORPHANS=1 uv run python lessons/15-data-engineering/code/03_delete_drill.py
Expect: clean deletion leaves zero residue in every store; with injection the
        drill reports orphaned rows in the answer cache and exits non-zero.
"""

# %% imports
import os
import sys
from dataclasses import dataclass, field

INJECT_ORPHANS = os.environ.get("INJECT_ORPHANS") == "1"


# %% derived_stores
@dataclass
class DerivedStores:
    """Everything a source document fans out into. In production these are separate systems."""

    chunks: dict[str, str] = field(default_factory=dict)  # chunk_id -> source_id
    embeddings: dict[str, str] = field(default_factory=dict)  # chunk_id -> source_id
    answer_cache: dict[str, str] = field(default_factory=dict)  # cache_key -> source_id that grounded the answer
    audit: list[str] = field(default_factory=list)

    def ingest(self, source_id: str, n_chunks: int) -> None:
        for i in range(n_chunks):
            cid = f"{source_id}#{i}"
            self.chunks[cid] = source_id
            self.embeddings[cid] = source_id
        self.answer_cache[f"q:{source_id}"] = source_id

    def delete_source(self, source_id: str) -> None:
        for store_name in ("chunks", "embeddings", "answer_cache"):
            if INJECT_ORPHANS and store_name == "answer_cache":
                continue  # the forgotten store
            store = getattr(self, store_name)
            for key in [k for k, v in store.items() if v == source_id]:
                del store[key]
        self.audit.append(f"deleted source {source_id}")

    def residue(self, source_id: str) -> dict[str, int]:
        return {
            name: sum(1 for v in getattr(self, name).values() if v == source_id)
            for name in ("chunks", "embeddings", "answer_cache")
        }


# %% run
def main() -> None:
    stores = DerivedStores()
    stores.ingest("policy/refund.md", 4)
    stores.ingest("hr/handbook.md", 6)
    stores.delete_source("policy/refund.md")
    residue = stores.residue("policy/refund.md")
    print(f"residue after deleting policy/refund.md: {residue}")
    print(f"other source untouched: {stores.residue('hr/handbook.md')}")
    print(f"audit: {stores.audit}")
    if any(residue.values()):
        print("DRILL FAILED: derived data survived the deletion; the pipeline is not erasure-safe")
        sys.exit(1)
    print("DRILL PASSED: no residue in any derived store")


if __name__ == "__main__":
    main()
