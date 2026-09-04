"""The same similarity table with a real embedding model. Optional; needs a key.

Uses the OpenAI-compatible /embeddings endpoint. DashScope's text-embedding-v3
and OpenAI's text-embedding-3-small both speak it. DeepSeek does not offer an
embeddings endpoint as of 2026-09-04, so this script defaults to DashScope.

Run:  MODEL_PROVIDER=dashscope uv run python lessons/04-embeddings-and-vector-search/code/04_real_embeddings.py
      MODEL_PROVIDER=openai    uv run python lessons/04-embeddings-and-vector-search/code/04_real_embeddings.py
Expect: the paraphrase now ranks high and the router question drops, the
        opposite of the toy vectors in 01.
"""

# %% imports
import asyncio
import math
import os

from openai import AsyncOpenAI

from aiapp.adapters.openai_compat import PRESETS

EMBEDDING_MODELS = {"dashscope": "text-embedding-v3", "openai": "text-embedding-3-small"}


# %% embed_via_api
async def embed_all(client: AsyncOpenAI, model: str, texts: list[str]) -> list[list[float]]:
    response = await client.embeddings.create(model=model, input=texts)
    return [row.embedding for row in sorted(response.data, key=lambda r: r.index)]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


# %% run
async def main() -> None:
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    if provider not in EMBEDDING_MODELS:
        print(f"MODEL_PROVIDER={provider!r} has no embedding model here. Use dashscope or openai with a key to run this.")
        return
    preset = PRESETS[provider]
    key = os.environ.get(preset.key_env)
    if not key:
        print(f"{preset.key_env} is not set; skipping the real embedding call.")
        return
    client = AsyncOpenAI(api_key=key, base_url=os.environ.get(f"{provider.upper()}_BASE_URL", preset.base_url))
    query = "how do I reset my password"
    candidates = [
        "steps to reset your password",
        "I forgot my login credentials, how can I get back in",
        "how do I reset my router",
        "quarterly revenue grew by twelve percent",
    ]
    vectors = await embed_all(client, EMBEDDING_MODELS[provider], [query, *candidates])
    print(f"model={EMBEDDING_MODELS[provider]} dim={len(vectors[0])}\n{'cosine':>7}  candidate")
    for text, vec in zip(candidates, vectors[1:]):
        print(f"{cosine(vectors[0], vec):7.3f}  {text}")


if __name__ == "__main__":
    asyncio.run(main())
