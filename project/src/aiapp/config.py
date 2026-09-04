"""Runtime settings, read from environment variables in one place and validated at startup.

Env vars (all optional):
  AIAPP_TOKENS           "token:tenant,token2:tenant2"  bearer tokens and the tenant each maps to
  AIAPP_PROMPT_VERSION   which prompts/assistant.<version>.md to use (default v1)
  AIAPP_MODEL_TIMEOUT_S  seconds to wait for the model's first chunk and between chunks (default 30)
  AIAPP_INJECT           failure injection: slow_model | provider_error (default none)
  DATABASE_URL           postgresql+asyncpg://user:pass@host/db; unset -> in-memory thread store
  REDIS_URL              redis://host:6379/0; unset -> in-memory key-value store
  AIAPP_RUN_LOCK_TTL_S   seconds a run may hold the per-thread lock (default 120)
  AIAPP_IDEMPOTENCY_TTL_S seconds an Idempotency-Key is remembered (default 86400)
  AIAPP_TOOL_ALLOWLIST   comma-separated tool names a request may use (default: every registered tool)
  AIAPP_SKILLS_DIR       directory of <skill>/SKILL.md (default project/skills)
  AIAPP_MCP_COMMAND      command line of a stdio MCP server to register, e.g. "python -m aiapp.mcp.toy_notes_server --read-only"
  AIAPP_MAX_STEPS / AIAPP_MAX_TOKENS / AIAPP_MAX_SECONDS   per-run budget (default 10 / 50000 / 120)
  AIAPP_CONTEXT_BUDGET_TOKENS  token budget for the assembled context window (default 24000)
  EMBEDDING_PROVIDER     fake (hashing, offline) | dashscope | openai   (default fake)
  AIAPP_CHUNK_MAX_CHARS  chunk size for ingestion (default 600)
  AIAPP_MEMORY_RECALL_K  memories injected per turn (default 5; 0 disables)
  AIAPP_ENV              development | production (production refuses default tokens and in-memory stores)
  OTEL_EXPORTER_OTLP_ENDPOINT  e.g. http://localhost:6006 (Phoenix); unset -> spans kept in memory
  AIAPP_RATE_LIMIT_RPS / AIAPP_RATE_LIMIT_BURST   per-tenant token bucket (default 5 / 20; 0 rps disables)
  AIAPP_DAILY_BUDGET_USD per-tenant daily budget; unset -> unlimited
  AIAPP_FALLBACK_PROVIDER  a second MODEL_PROVIDER used when the primary fails or the breaker is open
  AIAPP_PRICES_PATH      price table json (default aiapp/prices.json)
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_SKILLS_DIR = Path(__file__).resolve().parents[2] / "skills"

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
    database_url: str | None = None
    redis_url: str | None = None
    run_lock_ttl_s: int = 120
    idempotency_ttl_s: int = 86_400
    tool_allowlist: frozenset[str] | None = None  # None = every registered tool
    skills_dir: Path = DEFAULT_SKILLS_DIR
    mcp_command: str | None = None
    max_steps: int = 10
    max_tokens: int = 50_000
    max_seconds: float = 120.0
    context_budget_tokens: int = 24_000
    embedding_provider: str = "fake"
    chunk_max_chars: int = 600
    memory_recall_k: int = 5
    env: str = "development"
    otel_endpoint: str | None = None
    rate_limit_rps: float = 5.0
    rate_limit_burst: int = 20
    daily_budget_usd: float | None = None
    fallback_provider: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        env = os.environ if env is None else env
        return cls(
            tokens=parse_tokens(env.get("AIAPP_TOKENS")) or dict(DEFAULT_TOKENS),
            prompt_version=env.get("AIAPP_PROMPT_VERSION", "v1"),
            model_timeout_s=float(env.get("AIAPP_MODEL_TIMEOUT_S", "30")),
            inject=env.get("AIAPP_INJECT") or None,
            database_url=env.get("DATABASE_URL") or None,
            redis_url=env.get("REDIS_URL") or None,
            run_lock_ttl_s=int(env.get("AIAPP_RUN_LOCK_TTL_S", "120")),
            idempotency_ttl_s=int(env.get("AIAPP_IDEMPOTENCY_TTL_S", "86400")),
            tool_allowlist=frozenset(t.strip() for t in env["AIAPP_TOOL_ALLOWLIST"].split(",") if t.strip()) if env.get("AIAPP_TOOL_ALLOWLIST") else None,
            skills_dir=Path(env["AIAPP_SKILLS_DIR"]) if env.get("AIAPP_SKILLS_DIR") else DEFAULT_SKILLS_DIR,
            mcp_command=env.get("AIAPP_MCP_COMMAND") or None,
            max_steps=int(env.get("AIAPP_MAX_STEPS", "10")),
            max_tokens=int(env.get("AIAPP_MAX_TOKENS", "50000")),
            max_seconds=float(env.get("AIAPP_MAX_SECONDS", "120")),
            context_budget_tokens=int(env.get("AIAPP_CONTEXT_BUDGET_TOKENS", "24000")),
            embedding_provider=env.get("EMBEDDING_PROVIDER", "fake"),
            chunk_max_chars=int(env.get("AIAPP_CHUNK_MAX_CHARS", "600")),
            memory_recall_k=int(env.get("AIAPP_MEMORY_RECALL_K", "5")),
            env=env.get("AIAPP_ENV", "development"),
            otel_endpoint=env.get("OTEL_EXPORTER_OTLP_ENDPOINT") or None,
            rate_limit_rps=float(env.get("AIAPP_RATE_LIMIT_RPS", "5")),
            rate_limit_burst=int(env.get("AIAPP_RATE_LIMIT_BURST", "20")),
            daily_budget_usd=float(env["AIAPP_DAILY_BUDGET_USD"]) if env.get("AIAPP_DAILY_BUDGET_USD") else None,
            fallback_provider=env.get("AIAPP_FALLBACK_PROVIDER") or None,
        )

    def validate_for_production(self) -> list[str]:
        """What must be true before this configuration may serve real traffic. Empty list = fine."""
        problems = []
        if self.tokens == DEFAULT_TOKENS:
            problems.append("AIAPP_TOKENS is the development default")
        if not self.database_url:
            problems.append("DATABASE_URL is not set (threads would live in memory)")
        if not self.redis_url:
            problems.append("REDIS_URL is not set (locks and rate limits would be per-process)")
        if self.inject:
            problems.append(f"AIAPP_INJECT={self.inject!r} is a failure injection")
        return problems
