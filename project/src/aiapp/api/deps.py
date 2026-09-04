"""Dependencies injected into route handlers: settings, the tenant behind the bearer token, the store, the model."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request

from aiapp.adapters.base import ModelAdapter
from aiapp.api.errors import Unauthorized
from aiapp.config import Settings
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
