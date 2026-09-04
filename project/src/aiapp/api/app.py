"""Application factory. ``uvicorn aiapp.api.app:create_app --factory`` in production, ``create_app(...)`` in tests."""

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from aiapp.adapters import get_adapter
from aiapp.adapters.base import ModelAdapter
from aiapp.adapters.inject import apply_injection
from aiapp.api.errors import install_error_handlers
from aiapp.api.routes import health, threads
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
    if settings.redis_url:
        from aiapp.storage.redis_kv import RedisKeyValueStore

        kv: KeyValueStore = RedisKeyValueStore.from_url(settings.redis_url)
    else:
        kv = InMemoryKeyValueStore()
    return store, kv


def build_registry(settings: Settings, registry: ToolRegistry | None = None) -> tuple[ToolRegistry, SkillLoader, MCPToolSource | None]:
    """Local tools, then MCP tools, then the skill tools. All end up in one registry the runner guards the same way."""
    if registry is None:
        from aiapp.tools.demo import build_default_registry

        registry, _ = build_default_registry()
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
) -> FastAPI:
    settings = settings or Settings.from_env()
    model = apply_injection(model or get_adapter(), settings.inject)
    system_prompt = load_prompt("assistant", settings.prompt_version)  # fail at startup, not on the first request
    default_store, default_kv = build_stores(settings)
    store = store or default_store
    kv = kv or default_kv
    registry, skills, mcp = build_registry(settings, registry)
    runner = ToolRunner(registry, kv, result_ttl_s=settings.idempotency_ttl_s)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        if mcp:
            mcp.close()
        for resource in (store, kv):
            closer = getattr(resource, "dispose", None) or getattr(resource, "close", None)
            if closer:
                await closer()

    app = FastAPI(title="aiapp", version="0.3.0-m3", lifespan=lifespan)
    app.state.settings = settings
    app.state.model = model
    app.state.store = store
    app.state.kv = kv
    app.state.system_prompt = system_prompt
    app.state.registry = registry
    app.state.runner = runner
    app.state.skills = skills

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request.state.request_id)
        return response

    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(threads.router)
    log.info(
        "app ready model=%s prompt_version=%s inject=%s store=%s kv=%s tools=%s skills=%s",
        model.name, settings.prompt_version, settings.inject, type(store).__name__, type(kv).__name__,
        sorted(registry.names()), sorted(skills.skills),
    )
    return app
