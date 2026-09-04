"""Embedding adapters: the same protocol for a deterministic offline vector and real embedding APIs.

Every stored vector records which model produced it. Vectors from different
models live in different spaces and must never be compared, so every search
filters on the model name (the lesson 04 lesson learned the hard way).
"""

import hashlib
import math
import os
import re
from collections.abc import Sequence
from typing import Protocol

TOKEN = re.compile(r"[a-z0-9]+|[一-鿿]")


class EmbeddingAdapter(Protocol):
    name: str  # model identifier stored with every vector
    dim: int

    async def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


class HashingEmbedding:
    """Hashed bag of words with signed buckets, L2-normalised (lesson 13's construction). No semantics, fully offline."""

    def __init__(self, dim: int = 256):
        self.dim = dim
        self.name = f"hashing-{dim}"

    def embed_one(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0 if (h >> 8) % 2 else -1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed_one(t) for t in texts]


class OpenAICompatibleEmbedding:
    """/embeddings on an OpenAI-compatible endpoint (DashScope text-embedding-v3, OpenAI text-embedding-3-small, ...)."""

    def __init__(self, *, api_key: str, base_url: str, model: str, dim: int):
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.name = model
        self.dim = dim

    async def embed(self, texts: Sequence[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(model=self.name, input=list(texts))
        return [row.embedding for row in sorted(response.data, key=lambda r: r.index)]


EMBEDDING_PRESETS = {  # provider -> (model, dim), as of 2026-09-04; DeepSeek has no embeddings endpoint
    "dashscope": ("text-embedding-v3", 1024),
    "openai": ("text-embedding-3-small", 1536),
}


def get_embedding_adapter(provider: str | None = None) -> EmbeddingAdapter:
    provider = (provider or os.environ.get("EMBEDDING_PROVIDER") or "fake").lower()
    if provider == "fake":
        return HashingEmbedding()
    if provider not in EMBEDDING_PRESETS:
        raise ValueError(f"Unknown EMBEDDING_PROVIDER {provider!r}. Choose one of: fake, {', '.join(EMBEDDING_PRESETS)}.")
    from aiapp.adapters.openai_compat import PRESETS

    preset = PRESETS[provider]
    api_key = os.environ.get(preset.key_env)
    if not api_key:
        raise RuntimeError(f"{preset.key_env} is not set; use EMBEDDING_PROVIDER=fake or set the key.")
    model, dim = EMBEDDING_PRESETS[provider]
    return OpenAICompatibleEmbedding(api_key=api_key, base_url=os.environ.get(f"{provider.upper()}_BASE_URL", preset.base_url), model=os.environ.get("EMBEDDING_MODEL", model), dim=int(os.environ.get("EMBEDDING_DIM", dim)))


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / ((math.sqrt(sum(x * x for x in a)) or 1.0) * (math.sqrt(sum(y * y for y in b)) or 1.0))
