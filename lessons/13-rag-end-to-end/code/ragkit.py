"""Shared pieces for lesson 13, kept tiny and dependency-free.

Chunking, BM25, a toy hashed bag-of-words embedding (same construction as
lesson 04), cosine similarity and reciprocal-rank fusion. Each numbered
lesson file imports what it needs; this module has no side effects.
"""

import hashlib
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

CORPUS = Path(__file__).parent / "corpus"
TOKEN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Chunk:
    id: str  # "<doc>#<n>"
    doc: str
    text: str


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


# ---- chunking -------------------------------------------------------------------
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _units(text: str, max_chars: int) -> list[str]:
    """Paragraphs, except that a paragraph longer than max_chars is split into sentences."""
    units: list[str] = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para or para.startswith("#"):
            continue
        units += SENTENCE.split(para) if len(para) > max_chars else [para]
    return units


def chunk_document(doc: str, text: str, *, max_chars: int, overlap_paragraphs: int = 1) -> list[Chunk]:
    """Group whole units (paragraphs, or sentences when a paragraph is too long) up to max_chars,
    carrying the last N units into the next chunk as overlap."""
    paragraphs = _units(text, max_chars)
    chunks: list[Chunk] = []
    current: list[str] = []
    for para in paragraphs:
        if current and len("\n\n".join(current + [para])) > max_chars:
            chunks.append(Chunk(f"{doc}#{len(chunks)}", doc, "\n\n".join(current)))
            current = current[-overlap_paragraphs:] if overlap_paragraphs else []
        current.append(para)
    if current:
        chunks.append(Chunk(f"{doc}#{len(chunks)}", doc, "\n\n".join(current)))
    return chunks


def load_corpus(max_chars: int, **kw) -> list[Chunk]:
    out: list[Chunk] = []
    for path in sorted(CORPUS.glob("*.md")):
        out += chunk_document(path.stem, path.read_text(encoding="utf-8"), max_chars=max_chars, **kw)
    return out


# ---- BM25 (Robertson/Sparck Jones), about 25 lines -----------------------------------
class BM25:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(term for d in self.docs for term in d)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def score(self, query: str, i: int) -> float:
        d, dl = self.docs[i], self.lengths[i]
        s = 0.0
        for t in tokenize(query):
            if t not in d:
                continue
            tf = d[t]
            s += self.idf[t] * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_len))
        return s

    def rank(self, query: str) -> list[int]:
        return sorted(range(len(self.docs)), key=lambda i: -self.score(query, i))


# ---- toy embedding: hashed bag of words, 256 dims (lesson 04's construction) ------------
DIMS = 256


def embed(text: str) -> list[float]:
    v = [0.0] * DIMS
    for tok in tokenize(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
        v[h % DIMS] += 1.0 if (h >> 8) % 2 else -1.0
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def vector_rank(query: str, vectors: list[list[float]]) -> list[int]:
    q = embed(query)
    return sorted(range(len(vectors)), key=lambda i: -cosine(q, vectors[i]))


# ---- reciprocal rank fusion -------------------------------------------------------
def rrf(*rankings: list[int], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for pos, idx in enumerate(ranking):
            scores[idx] = scores.get(idx, 0.0) + 1.0 / (k + pos + 1)
    return sorted(scores, key=lambda i: -scores[i])
