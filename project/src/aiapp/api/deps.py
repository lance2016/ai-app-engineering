"""Dependencies injected into route handlers: settings, the tenant behind the bearer token, the store, the model."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request

from aiapp.adapters.base import ModelAdapter
from aiapp.api.errors import Unauthorized
from aiapp.config import Settings
from aiapp.knowledge.memory import MemoryService
from aiapp.ops.cost import CostLedger
from aiapp.ops.ratelimit import RateLimiter
from aiapp.knowledge.retriever import Retriever
from aiapp.runtime import SkillLoader, ToolRunner
from aiapp.storage.base import KeyValueStore, ThreadStore


@dataclass(frozen=True)
class Tenant:
    id: str


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> ThreadStore:
    return request.app.state.store


def get_kv(request: Request) -> KeyValueStore:
    return request.app.state.kv


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_cost_ledger(request: Request) -> CostLedger:
    return request.app.state.cost_ledger


def get_retriever(request: Request) -> Retriever:
    return request.app.state.retriever


def get_memory(request: Request) -> MemoryService:
    return request.app.state.memory


def get_runner(request: Request) -> ToolRunner:
    return request.app.state.runner


def get_skills(request: Request) -> SkillLoader:
    return request.app.state.skills


def get_model(request: Request) -> ModelAdapter:
    return request.app.state.model


def get_system_prompt(request: Request) -> str:
    return request.app.state.system_prompt


def get_tenant(
    settings: Annotated[Settings, Depends(get_settings)],
    authorization: Annotated[str | None, Header()] = None,
) -> Tenant:
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    tenant_id = settings.tokens.get(token)
    if tenant_id is None:
        raise Unauthorized("invalid token")
    return Tenant(id=tenant_id)


def get_user_id(tenant: Annotated[Tenant, Depends(get_tenant)], x_user_id: Annotated[str | None, Header()] = None) -> str:
    """The end user behind the request, for memory scoping. Defaults to the tenant itself (single-user tenants)."""
    return (x_user_id or "").strip() or tenant.id
