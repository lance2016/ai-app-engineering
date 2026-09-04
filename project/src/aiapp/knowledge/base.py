"""Types and the storage protocol for the knowledge layer."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class Document:
    doc_id: str
    version: int
    text: str
    title: str = ""


@dataclass(frozen=True)
class Chunk:
    """A contiguous slice of a document version: ``text == document.text[start:end]``, so a citation can point at the source."""

    chunk_id: str  # "<doc_id>#<n>"
    doc_id: str
    version: int
    section: str
    start: int
    end: int
    text: str
    content_hash: str


@dataclass(frozen=True)
class Hit:
    chunk_id: str
    doc_id: str
    version: int
    section: str
    start: int
    end: int
    text: str
    score: float
    source: str = "hybrid"  # vector | text | hybrid

    @property
    def citation_id(self) -> str:
        return f"{self.doc_id}@v{self.version}#{self.chunk_id.rsplit('#', 1)[1]}"


@dataclass
class IngestReport:
    doc_id: str
    version: int
    chunks: int
    embedded: int  # chunks that needed a new vector
    reused: int  # chunks whose content hash was already indexed (vector kept)
    removed: int  # chunks of the previous version that no longer exist
    problems: list[str] = field(default_factory=list)


class KnowledgeStore(Protocol):
    async def upsert_document(self, tenant_id: str, doc: Document, chunks: list[Chunk], vectors: list[list[float] | None], embedding_model: str) -> IngestReport:
        """Replace the document's indexed version. ``vectors[i] is None`` means "keep the vector already stored for this content hash"."""
        ...

    async def existing_hashes(self, tenant_id: str, doc_id: str) -> set[str]:
        """Content hashes currently indexed for this document (so unchanged chunks are not re-embedded)."""
        ...

    async def search_vector(self, tenant_id: str, query_vector: list[float], *, k: int, embedding_model: str) -> list[Hit]: ...

    async def search_text(self, tenant_id: str, query: str, *, k: int) -> list[Hit]: ...

    async def delete_document(self, tenant_id: str, doc_id: str) -> int:
        """Remove the document and everything derived from it. Returns the number of chunks removed."""
        ...

    async def list_documents(self, tenant_id: str) -> list[tuple[str, int, str]]:
        """(doc_id, version, title) for the tenant."""
        ...

    async def residue(self, tenant_id: str, doc_id: str) -> dict[str, int]:
        """What is left of a document in every derived store. All zeros after a clean delete (lesson 15 drill)."""
        ...
