"""Runtime settings, read from environment variables in one place and validated at startup.

Env vars (all optional):
  AIAPP_TOKENS           "token:tenant,token2:tenant2"  bearer tokens and the tenant each maps to
  AIAPP_PROMPT_VERSION   which prompts/assistant.<version>.md to use (default v1)
  AIAPP_MODEL_TIMEOUT_S  seconds to wait for the model's first chunk and between chunks (default 30)
  AIAPP_INJECT           failure injection: slow_model | provider_error (default none)
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

DEFAULT_TOKENS = {"dev-token": "tenant-demo"}  # development only; production sets AIAPP_TOKENS


def parse_tokens(raw: str | None) -> dict[str, str]:
    """'tok1:tenant-a,tok2:tenant-b' -> {'tok1': 'tenant-a', 'tok2': 'tenant-b'}."""
    if not raw or not raw.strip():
        return {}
    tokens: dict[str, str] = {}
    for entry in raw.split(","):
        token, sep, tenant = entry.strip().partition(":")
        if not sep or not token or not tenant:
            raise ValueError(f"AIAPP_TOKENS entry {entry!r} must look like 'token:tenant'")
        tokens[token] = tenant
    return tokens


@dataclass(frozen=True)
class Settings:
    tokens: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_TOKENS))
    prompt_version: str = "v1"
    model_timeout_s: float = 30.0
    inject: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        return cls(
            tokens=parse_tokens(env.get("AIAPP_TOKENS")) or dict(DEFAULT_TOKENS),
            prompt_version=env.get("AIAPP_PROMPT_VERSION", "v1"),
            model_timeout_s=float(env.get("AIAPP_MODEL_TIMEOUT_S", "30")),
            inject=env.get("AIAPP_INJECT") or None,
        )
