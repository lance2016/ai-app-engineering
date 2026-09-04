"""Knowledge: documents in, chunks with provenance indexed, hybrid retrieval out, citations verified; plus per-user memory."""

from aiapp.knowledge.base import Chunk, Document, Hit, KnowledgeStore
from aiapp.knowledge.ingest import chunk_document, parse_markdown
from aiapp.knowledge.retriever import Retriever

__all__ = ["Chunk", "Document", "Hit", "KnowledgeStore", "Retriever", "chunk_document", "parse_markdown"]
