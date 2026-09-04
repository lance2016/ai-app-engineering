"""Adapter factory. Selects the provider from ``MODEL_PROVIDER`` (or the argument).

Reads ``.env`` from the repository root so lesson scripts can be run from anywhere.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from aiapp.adapters.base import ModelAdapter
from aiapp.adapters.fake import FakeAdapter
from aiapp.adapters.openai_compat import PRESETS, OpenAICompatibleAdapter

_REPO_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_REPO_ROOT / ".env")


def get_adapter(provider: str | None = None, *, model: str | None = None) -> ModelAdapter:
    provider = (provider or os.environ.get("MODEL_PROVIDER") or "fake").lower()
    if provider == "fake":
        return FakeAdapter()
    preset = PRESETS.get(provider)
    if preset is None:
        raise ValueError(f"Unknown provider {provider!r}. Choose one of: fake, {', '.join(PRESETS)}.")
    api_key = os.environ.get(preset.key_env)
    if not api_key:
        raise RuntimeError(f"{preset.key_env} is not set. Copy .env.example to .env and fill it in, or use MODEL_PROVIDER=fake.")
    return OpenAICompatibleAdapter(
        name=provider,
        api_key=api_key,
        base_url=os.environ.get(f"{provider.upper()}_BASE_URL", preset.base_url),
        model=model or os.environ.get(f"{provider.upper()}_MODEL", preset.default_model),
    )
