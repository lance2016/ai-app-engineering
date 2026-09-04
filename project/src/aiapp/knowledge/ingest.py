"""Parse a Markdown document into heading-aware, size-capped chunks that know exactly where they came from.

Chunks are contiguous slices of the document text (``start``/``end`` offsets),
never cross a heading, and carry a content hash. Unchanged text keeps its hash
across versions, which is what makes re-ingestion incremental (lesson 15).
"""

import hashlib
import re

from aiapp.knowledge.base import Chunk, Document

HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.M)
PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


def parse_markdown(doc_id: str, text: str, *, version: int = 1, title: str | None = None) -> Document:
    if title is None:
        m = HEADING.search(text)
        title = m.group(1).strip() if m else doc_id
    return Document(doc_id=doc_id, version=version, text=text, title=title)


def _sections(text: str) -> list[tuple[str, int, int]]:
    """(heading, start, end) spans covering the whole text; text before the first heading is 'root'."""
    marks = [(m.start(), m.group(1).strip()) for m in HEADING.finditer(text)]
    spans: list[tuple[str, int, int]] = []
    cursor, heading = 0, "root"
    for pos, title in marks:
        if pos > cursor:
            spans.append((heading, cursor, pos))
        cursor, heading = pos, title
    spans.append((heading, cursor, len(text)))
    return [(h, s, e) for h, s, e in spans if text[s:e].strip()]


def _paragraph_spans(text: str, start: int, end: int) -> list[tuple[int, int]]:
    spans, cursor = [], start
    for m in PARAGRAPH_BREAK.finditer(text, start, end):
        if m.start() > cursor:
            spans.append((cursor, m.start()))
        cursor = m.end()
    if end > cursor:
        spans.append((cursor, end))
    return [(s, e) for s, e in spans if text[s:e].strip()]


def content_hash(doc_id: str, section: str, text: str) -> str:
    return hashlib.sha256(f"{doc_id}|{section}|{text.strip()}".encode()).hexdigest()[:16]


def chunk_document(doc: Document, *, max_chars: int = 600) -> list[Chunk]:
    """Group whole paragraphs inside one section up to ``max_chars``; a paragraph longer than that becomes its own chunk."""
    chunks: list[Chunk] = []

    def emit(section: str, start: int, end: int) -> None:
        text = doc.text[start:end]
        chunks.append(Chunk(f"{doc.doc_id}#{len(chunks)}", doc.doc_id, doc.version, section, start, end, text, content_hash(doc.doc_id, section, text)))

    for section, s_start, s_end in _sections(doc.text):
        group_start: int | None = None
        group_end = s_start
        for p_start, p_end in _paragraph_spans(doc.text, s_start, s_end):
            if group_start is not None and p_end - group_start > max_chars:
                emit(section, group_start, group_end)
                group_start = None
            if group_start is None:
                group_start = p_start
            group_end = p_end
        if group_start is not None:
            emit(section, group_start, group_end)
    return chunks


def quality_problems(chunks: list[Chunk]) -> list[str]:
    seen: set[str] = set()
    problems = []
    for c in chunks:
        if "�" in c.text:
            problems.append(f"{c.chunk_id}: replacement character (bad encoding) in section {c.section!r}")
        if c.content_hash in seen:
            problems.append(f"{c.chunk_id}: duplicate of an earlier chunk in section {c.section!r}")
        seen.add(c.content_hash)
    return problems
