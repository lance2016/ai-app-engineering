"""Application factory. ``uvicorn aiapp.api.app:create_app --factory`` in production, ``create_app(...)`` in tests."""

import logging
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from aiapp.adapters import get_adapter
from aiapp.adapters.base import ModelAdapter
from aiapp.adapters.inject import apply_injection
from aiapp.api.errors import install_error_handlers
from aiapp.api.routes import health, threads
from aiapp.config import Settings
from aiapp.prompts import load_prompt
from aiapp.storage import InMemoryThreadStore
from aiapp.storage.base import ThreadStore

log = logging.getLogger("aiapp.api")


def create_app(
    settings: Settings | None = None,
    model: ModelAdapter | None = None,
    store: ThreadStore | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()
    model = apply_injection(model or get_adapter(), settings.inject)
    system_prompt = load_prompt("assistant", settings.prompt_version)  # fail at startup, not on the first request

    app = FastAPI(title="aiapp", version="0.1.0-m1")
    app.state.settings = settings
    app.state.model = model
    app.state.store = store or InMemoryThreadStore()
    app.state.system_prompt = system_prompt

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers.setdefault("X-Request-ID", request.state.request_id)
        return response

    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(threads.router)
    log.info("app ready model=%s prompt_version=%s inject=%s", model.name, settings.prompt_version, settings.inject)
    return app
