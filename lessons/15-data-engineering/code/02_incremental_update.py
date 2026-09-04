"""Re-ingesting a changed document touches only the chunks that changed.

The index is keyed by content hash. When a source is re-ingested at a new
version, unchanged chunks are kept, changed ones are replaced, and chunks that
no longer exist in the source are removed. Freshness is a property of the
index you can query, not something you hope for.

Run:  uv run python lessons/15-data-engineering/code/02_incremental_update.py
Expect: version 2 changes one section and drops another; the index reports 2 unchanged,
        1 embedded, 2 removed (the replaced old version counts as removed), and the
        stale-check flags nothing after the update.
"""

# %% imports
import hashlib
from dataclasses import dataclass, replace
from datetime import date


# %% index
@dataclass(frozen=True)
class IndexedChunk:
    content_hash: str
    source_id: str
    source_version: int
    section: str
    text: str
    embedded_on: date  # stands in for "when the expensive part ran"


class Index:
    def __init__(self) -> None:
        self.by_hash: dict[str, IndexedChunk] = {}
        self.source_versions: dict[str, int] = {}

    def upsert_source(self, source_id: str, version: int, sections: dict[str, str], *, today: date) -> dict[str, int]:
        incoming = {}
        for section, text in sections.items():
            h = hashlib.sha256(f"{source_id}|{section}|{text}".encode()).hexdigest()[:12]
            incoming[h] = IndexedChunk(h, source_id, version, section, text, today)
        current = {h: c for h, c in self.by_hash.items() if c.source_id == source_id}
        unchanged = set(incoming) & set(current)
        added = set(incoming) - set(current)
        removed = set(current) - set(incoming)
        for h in removed:
            del self.by_hash[h]
        for h in added:
            self.by_hash[h] = incoming[h]  # only these would be embedded
        for h in unchanged:
            self.by_hash[h] = replace(self.by_hash[h], source_version=version)  # still valid at the new version, no re-embedding
        self.source_versions[source_id] = version
        return {"unchanged": len(unchanged), "embedded": len(added), "removed": len(removed)}

    def stale_chunks(self) -> list[IndexedChunk]:
        """Chunks whose recorded version is behind the source's current version."""
        return [c for c in self.by_hash.values() if c.source_version < self.source_versions.get(c.source_id, c.source_version)]


# %% versions
V1 = {
    "Refund Policy": "Customers may request a refund within 30 days of purchase.",
    "Digital goods": "Digital goods are refundable only if not downloaded.",
    "Physical goods": "Physical goods must be returned unused. Shipping is not refunded.",
    "Contact": "Email support@example.com for refund requests.",
}
V2 = {**V1, "Digital goods": "Digital goods are refundable within 14 days, even if downloaded."}
del V2["Contact"]  # section removed in the new version


# %% run
def main() -> None:
    idx = Index()
    print("ingest v1:", idx.upsert_source("policy/refund.md", 1, V1, today=date(2026, 8, 1)))
    print("ingest v2:", idx.upsert_source("policy/refund.md", 2, V2, today=date(2026, 9, 4)))
    for c in sorted(idx.by_hash.values(), key=lambda c: c.section):
        print(f"  {c.content_hash} [{c.section:14}] embedded {c.embedded_on}  {c.text[:45]!r}")
    print("stale:", [c.section for c in idx.stale_chunks()])
    assert len(idx.by_hash) == 3 and not idx.stale_chunks()


if __name__ == "__main__":
    main()
