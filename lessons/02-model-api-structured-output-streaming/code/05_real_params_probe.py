"""Optional: see temperature and max_tokens do something on a real model.

Calls the OpenAI-compatible endpoint directly (this lesson is about the API
itself) with the same prompt at two temperatures, three times each. Needs a
key; without one it prints a hint and exits.

Run:  MODEL_PROVIDER=deepseek uv run python lessons/02-model-api-structured-output-streaming/code/05_real_params_probe.py
Expect: near-identical answers at temperature 0, varied ones at 1.3, and a
        truncated answer when max_tokens is tiny (finish_reason=length).
"""

# %% imports
import asyncio
import os

from openai import AsyncOpenAI

from aiapp.adapters.openai_compat import PRESETS

PROMPT = "Name one animal. Reply with a single word."


# %% probe
async def probe(client: AsyncOpenAI, model: str, *, temperature: float, max_tokens: int, runs: int) -> None:
    answers = []
    finish = None
    for _ in range(runs):
        r = await client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": PROMPT}], temperature=temperature, max_tokens=max_tokens
        )
        answers.append((r.choices[0].message.content or "").strip())
        finish = r.choices[0].finish_reason
    print(f"temperature={temperature} max_tokens={max_tokens}: {answers} finish_reason={finish}")


# %% run
async def main() -> None:
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    preset = PRESETS.get(provider)
    key = os.environ.get(preset.key_env) if preset else None
    if not preset or not key:
        print("set MODEL_PROVIDER=deepseek (or dashscope/openai) and its API key to run this probe.")
        return
    client = AsyncOpenAI(api_key=key, base_url=os.environ.get(f"{provider.upper()}_BASE_URL", preset.base_url))
    model = os.environ.get(f"{provider.upper()}_MODEL", preset.default_model)
    await probe(client, model, temperature=0.0, max_tokens=20, runs=3)
    await probe(client, model, temperature=1.3, max_tokens=20, runs=3)
    await probe(client, model, temperature=0.0, max_tokens=2, runs=1)


if __name__ == "__main__":
    asyncio.run(main())
