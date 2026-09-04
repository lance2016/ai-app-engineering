"""Reciprocal rank fusion: combine rankings without calibrating their scores against each other."""

from aiapp.knowledge.base import Hit


def rrf(*rankings: list[Hit], k: int = 60, limit: int | None = None) -> list[Hit]:
    scores: dict[str, float] = {}
    hits: dict[str, Hit] = {}
    for ranking in rankings:
        for pos, hit in enumerate(ranking):
            scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + pos + 1)
            hits.setdefault(hit.chunk_id, hit)
    fused = sorted(scores, key=lambda cid: -scores[cid])
    out = [Hit(**{**hits[cid].__dict__, "score": round(scores[cid], 6), "source": "hybrid"}) for cid in fused]
    return out[:limit] if limit else out
