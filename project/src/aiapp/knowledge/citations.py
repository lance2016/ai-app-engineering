"""Citations the model writes are claims; the runtime verifies them (lesson 13, step seven).

A citation must name a chunk that was actually retrieved in this run, and the
sentence it supports must share words with that chunk. A made-up citation is
the RAG equivalent of a hallucinated tool call: it looks right and is caught by code.
"""

import re
from dataclasses import dataclass, field

from aiapp.adapters.embeddings import tokenize
from aiapp.knowledge.base import Hit

CITATION = re.compile(r"\[([A-Za-z0-9_\-./]+@v\d+#\d+)\]")
STOPWORDS = {"the", "a", "an", "is", "are", "to", "of", "and", "for", "in", "on", "with", "you", "your", "it", "be", "can", "will"}


@dataclass
class CitationReport:
    cited: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict:
        return {"ok": self.ok, "cited": self.cited, "problems": self.problems}


def verify_citations(answer: str, retrieved: list[Hit] | dict[str, str], *, min_overlap: int = 2) -> CitationReport:
    by_id = {h.citation_id: h.text for h in retrieved} if isinstance(retrieved, list) else dict(retrieved)
    report = CitationReport()
    for sentence in re.split(r"(?<=[.!?。！？])\s*", answer):
        for cid in CITATION.findall(sentence):
            if cid not in report.cited:
                report.cited.append(cid)
            source = by_id.get(cid)
            if source is None:
                report.problems.append(f"[{cid}] was never retrieved in this run")
                continue
            words = set(tokenize(CITATION.sub("", sentence))) - STOPWORDS
            if words and len(words & set(tokenize(source))) < min_overlap:
                report.problems.append(f"[{cid}] does not support: {sentence.strip()[:80]!r}")
    if by_id and not report.cited:
        report.problems.append("sources were retrieved but the answer cites none of them")
    return report


def render_sources(hits: list[Hit]) -> str:
    """What the model sees: one block per hit, keyed by the citation id it must use."""
    return "\n\n".join(f"[{h.citation_id}] ({h.section})\n{h.text.strip()}" for h in hits)
