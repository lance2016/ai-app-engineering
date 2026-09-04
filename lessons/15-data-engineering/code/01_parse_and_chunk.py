"""From a document to chunks that carry their own metadata.

Parsing splits a markdown file by headings; chunking caps size while keeping
each chunk inside one section. Every chunk records where it came from, which
version of the source it reflects, who may see it, and a content hash. Quality
checks reject empty, duplicated or mis-encoded chunks before they reach an index.

Run:  uv run python lessons/15-data-engineering/code/01_parse_and_chunk.py
      INJECT_BAD_INPUT=1 uv run python lessons/15-data-engineering/code/01_parse_and_chunk.py
Expect: 5 clean chunks with metadata; with injection two quality problems are reported and dropped.
"""

# %% imports
import hashlib
import os
import re
from dataclasses import dataclass, field

INJECT_BAD_INPUT = os.environ.get("INJECT_BAD_INPUT") == "1"
MAX_CHUNK_CHARS = 200


# %% source_document
DOC = """# Refund Policy
Customers may request a refund within 30 days of purchase.
## Digital goods
Digital goods are refundable only if not downloaded.
## Physical goods
Physical goods must be returned unused. Shipping is not refunded.
## Contact
Email support@example.com for refund requests.
"""
ACL = ("customers", "support")  # who may see chunks derived from this document


# %% types
@dataclass(frozen=True)
class Chunk:
    source_id: str
    source_version: int
    section: str
    text: str
    acl: tuple[str, ...]
    content_hash: str = field(default="")

    def with_hash(self) -> "Chunk":
        h = hashlib.sha256(f"{self.source_id}|{self.section}|{self.text}".encode()).hexdigest()[:12]
        return Chunk(self.source_id, self.source_version, self.section, self.text, self.acl, h)


# %% parse_and_chunk
def parse_sections(markdown: str) -> list[tuple[str, str]]:
    """Split by headings. PDFs, DOCX and scans need a real parser (Docling, Unstructured); the shape of the output is the same."""
    sections: list[tuple[str, str]] = []
    title, buf = "root", []
    for line in markdown.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if buf:
                sections.append((title, "\n".join(buf).strip()))
            title, buf = line.lstrip("# ").strip(), []
        else:
            buf.append(line)
    if buf:
        sections.append((title, "\n".join(buf).strip()))
    return sections


def chunk(source_id: str, version: int, markdown: str, acl: tuple[str, ...]) -> list[Chunk]:
    chunks = []
    for section, text in parse_sections(markdown):
        for start in range(0, max(len(text), 1), MAX_CHUNK_CHARS):  # never cross a section boundary
            chunks.append(Chunk(source_id, version, section, text[start:start + MAX_CHUNK_CHARS], acl).with_hash())
    return chunks


# %% quality_checks
def quality_check(chunks: list[Chunk]) -> tuple[list[Chunk], list[str]]:
    seen: set[str] = set()
    kept, problems = [], []
    for c in chunks:
        if not c.text.strip():
            problems.append(f"empty chunk in section {c.section!r}")
            continue
        if "�" in c.text:
            problems.append(f"replacement character (bad encoding) in section {c.section!r}")
            continue
        if c.content_hash in seen:
            problems.append(f"duplicate chunk {c.content_hash} in section {c.section!r}")
            continue
        seen.add(c.content_hash)
        kept.append(c)
    return kept, problems


# %% run
def main() -> None:
    doc = DOC
    if INJECT_BAD_INPUT:
        doc += "## Empty section\n\n## Garbled\nRefunds are pro�essed weekly.\n## Digital goods\nDigital goods are refundable only if not downloaded.\n"
    chunks, problems = quality_check(chunk("policy/refund.md", 1, doc, ACL))
    for c in chunks:
        print(f"{c.content_hash} v{c.source_version} [{c.section:15}] acl={c.acl} {c.text[:50]!r}")
    for p in problems:
        print(f"DROPPED: {p}")
    print(f"{len(chunks)} chunks kept, {len(problems)} dropped")


if __name__ == "__main__":
    main()
