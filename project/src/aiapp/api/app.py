"""Application factory. ``uvicorn aiapp.api.app:create_app --factory`` in production, ``create_app(...)`` in tests."""

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from aiapp.adapters import get_adapter
from aiapp.adapters.base import ModelAdapter
from aiapp.adapters.embeddings import get_embedding_adapter
from aiapp.adapters.inject import apply_injection
from aiapp.api.errors import install_error_handlers
from aiapp.api.routes import health, knowledge, threads
from aiapp.ops import telemetry
from aiapp.ops.cost import CostLedger, CostStore, InMemoryCostStore, PriceTable
from aiapp.ops.logging import setup_logging
from aiapp.ops.ratelimit import InMemoryRateLimiter, RateLimiter
from aiapp.ops.resilience import CircuitBreaker, FallbackAdapter
from decimal import Decimal
from aiapp.knowledge.memory import InMemoryMemoryStore, MemoryService, MemoryStore
from aiapp.knowledge.memory_store import InMemoryKnowledgeStore
from aiapp.knowledge.base import KnowledgeStore
from aiapp.knowledge.retriever import Retriever
from aiapp.tools.knowledge import register_knowledge_tool
from aiapp.config import Settings
from aiapp.prompts import load_prompt
from aiapp.runtime import SkillLoader, ToolRegistry, ToolRunner
from aiapp.runtime.mcp_source import MCPToolSource
from aiapp.storage import InMemoryKeyValueStore, InMemoryThreadStore
from aiapp.storage.base import KeyValueStore, ThreadStore

log = logging.getLogger("aiapp.api")


def build_stores(settings: Settings) -> tuple[ThreadStore, KeyValueStore]:
    """PostgreSQL and Redis when configured, in-memory otherwise. Both pairs pass the same contract tests."""
    if settings.database_url:
        from aiapp.storage.postgres import PostgresThreadStore

        store: ThreadStore = PostgresThreadStore.from_url(settings.database_url)
    else:
        store = InMemoryThreadStore()
    return store, _build_kv(settings)


def build_ops(settings: Settings) -> tuple[RateLimiter, CostStore]:
    if settings.redis_url:
        from aiapp.ops.ratelimit import RedisRateLimiter

        limiter: RateLimiter = RedisRateLimiter.from_url(settings.redis_url)
    else:
        limiter = InMemoryRateLimiter()
    if settings.database_url:
        from aiapp.ops.postgres_cost import PostgresCostStore

        cost_store: CostStore = PostgresCostStore.from_url(settings.database_url)
    else:
        cost_store = InMemoryCostStore()
    return limiter, cost_store


def build_model(settings: Settings, model: ModelAdapter | None) -> ModelAdapter:
    """Primary (with any injection applied) behind a breaker and a fallback when one is configured."""
    primary = apply_injection(model or get_adapter(), settings.inject)
    if not settings.fallback_provider:
        return primary
    secondary = get_adapter(settings.fallback_provider)
    return FallbackAdapter(primary, secondary, CircuitBreaker(failure_threshold=3, recovery_timeout_s=30.0), primary_timeout_s=settings.model_timeout_s)


def build_knowledge(settings: Settings) -> tuple[KnowledgeStore, MemoryStore]:
    if settings.database_url:
        from aiapp.knowledge.postgres_memory import PostgresMemoryStore
        from aiapp.knowledge.postgres_store import PostgresKnowledgeStore

        return PostgresKnowledgeStore.from_url(settings.database_url), PostgresMemoryStore.from_url(settings.database_url)
    return InMemoryKnowledgeStore(), InMemoryMemoryStore()


def _build_kv(settings: Settings) -> KeyValueStore:
    if settings.redis_url:
        from aiapp.storage.redis_kv import RedisKeyValueStore

        return RedisKeyValueStore.from_url(settings.redis_url)
    return InMemoryKeyValueStore()


def build_registry(settings: Settings, registry: ToolRegistry | None = None, retriever: Retriever | None = None) -> tuple[ToolRegistry, SkillLoader, MCPToolSource | None]:
    """Local tools, the knowledge tool, MCP tools, then the skill tools. All end up in one registry the runner guards the same way."""
    if registry is None:
        from aiapp.tools.demo import build_default_registry

        registry, _ = build_default_registry()
    if retriever is not None:
        register_knowledge_tool(registry, retriever)
    mcp = None
    if settings.mcp_command:
        mcp = MCPToolSource.from_command_line(settings.mcp_command)
        mcp.register_into(registry)
    skills = SkillLoader(settings.skills_dir).discover(registry.names())
    skills.register_into(registry)
    return registry, skills, mcp


def create_app(
    settings: Settings | None = None,
    model: ModelAdapter | None = None,
    store: ThreadStore | None = None,
    kv: KeyValueStore | None = None,
    registry: ToolRegistry | None = None,
    knowledge_store: KnowledgeStore | None = None,
    memory_store: MemoryStore | None = None,
    rate_limiter: RateLimiter | None = None,
    cost_store: CostStore | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    if settings.env == "production" and (problems := settings.validate_for_production()):
        raise RuntimeError("refusing to start in production: " + "; ".join(problems))
    telemetry.setup_tracing(settings.otel_endpoint)
    if settings.env == "production":
        setup_logging()
    model = build_model(settings, model)
    system_prompt = load_prompt("assistant", settings.prompt_version)  # fail at startup, not on the first request
    default_store, default_kv = build_stores(settings)
    store = store or default_store
    kv = kv or default_kv
    default_knowledge, default_memory = build_knowledge(settings)
    embedder = get_embedding_adapter(settings.embedding_provider)
    retriever = Retriever(knowledge_store or default_knowledge, embedder, max_chars=settings.chunk_max_chars)
    memory = MemoryService(memory_store or default_memory, embedder)
    registry, skills, mcp = build_registry(settings, registry, retriever)
    runner = ToolRunner(registry, kv, result_ttl_s=settings.idempotency_ttl_s)
    default_limiter, default_cost_store = build_ops(settings)
    rate_limiter = rate_limiter or default_limiter
    cost_ledger = CostLedger(cost_store or default_cost_store, PriceTable.load(), Decimal(str(settings.daily_budget_usd)) if settings.daily_budget_usd is not None else None)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if mcp:
            mcp.close()
        for resource in (store, kv, retriever.store, memory.store, rate_limiter, cost_ledger.store):
            closer = getattr(resource, "dispose", None) or getattr(resource, "close", None)
            if closer:
                await closer()

    app = FastAPI(title="aiapp", version="0.5.0-m5", lifespan=lifespan)
    app.state.settings = settings
    app.state.model = model
    app.state.store = store
    app.state.kv = kv
    app.state.system_prompt = system_prompt
    app.state.registry = registry
    app.state.runner = runner
    app.state.skills = skills
    app.state.retriever = retriever
    app.state.memory = memory
    app.state.rate_limiter = rate_limiter
    app.state.cost_ledger = cost_ledger

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        with telemetry.tracer().start_as_current_span(f"{request.method} {request.url.path}", attributes={"http.request.method": request.method, "url.path": request.url.path, telemetry.A_REQUEST_ID: request.state.request_id, telemetry.A_PROMPT_VERSION: settings.prompt_version}) as span:
            response = await call_next(request)
            span.set_attribute("http.response.status_code", response.status_code)
            if response.status_code >= 500:
                telemetry.mark_error(span, f"HTTP {response.status_code}")
        response.headers.setdefault("X-Request-ID", request.state.request_id)
        return response

    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(threads.router)
    app.include_router(knowledge.router)
    log.info(
        "app ready model=%s prompt_version=%s inject=%s store=%s kv=%s tools=%s skills=%s",
        model.name, settings.prompt_version, settings.inject, type(store).__name__, type(kv).__name__,
        sorted(registry.names()), sorted(skills.skills),
    )
    return app
