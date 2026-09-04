"""Threads: create one, read it back, send a message and watch the run as server-sent events."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from aiapp.adapters.base import ModelAdapter
from aiapp.api.deps import Tenant, get_model, get_settings, get_store, get_system_prompt, get_tenant
from aiapp.api.errors import ModelTimeout, NotFound, ProviderError, request_id_of
from aiapp.api.schemas import CreateThreadRequest, MessageRequest, ThreadView
from aiapp.config import Settings
from aiapp.runtime import Delta, run_turn
from aiapp.storage.base import ThreadNotFound, ThreadStore
from aiapp.thread import Event, Thread

log = logging.getLogger("aiapp.api")
router = APIRouter(prefix="/v1/threads", tags=["threads"])


async def _load(store: ThreadStore, thread_id: str, tenant: Tenant) -> Thread:
    try:
        return await store.load(thread_id, tenant_id=tenant.id)
    except ThreadNotFound:
        raise NotFound(f"thread {thread_id} not found") from None


@router.post("", status_code=201, response_model=ThreadView)
async def create_thread(
    body: CreateThreadRequest,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
) -> ThreadView:
    thread = await store.create(tenant.id)
    if body.title:
        thread.append("thread_created", title=body.title)
    await store.save(thread)
    return ThreadView.from_thread(thread, tenant.id)


@router.get("/{thread_id}", response_model=ThreadView)
async def read_thread(
    thread_id: str,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
) -> ThreadView:
    return ThreadView.from_thread(await _load(store, thread_id, tenant), tenant.id)


def sse_frame(item: Event | Delta) -> str:
    """``event: <type>\\ndata: <json>\\n\\n`` — thread events keep their type; deltas are ``assistant_delta``."""
    if isinstance(item, Delta):
        return f"event: assistant_delta\ndata: {json.dumps({'content': item.content}, ensure_ascii=False)}\n\n"
    return f"event: {item.type}\ndata: {json.dumps(item.data, ensure_ascii=False)}\n\n"


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    body: MessageRequest,
    request: Request,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
    model: Annotated[ModelAdapter, Depends(get_model)],
    settings: Annotated[Settings, Depends(get_settings)],
    system_prompt: Annotated[str, Depends(get_system_prompt)],
) -> StreamingResponse:
    thread = await _load(store, thread_id, tenant)
    request_id = request_id_of(request)
    turn = run_turn(thread, model, system_prompt=system_prompt, user_content=body.content, timeout_s=settings.model_timeout_s)

    # Reach the model's first chunk before committing to a 200: a timeout or outage here is a real status code.
    try:
        first = await anext(turn)
    except TimeoutError:
        await store.save(thread)
        raise ModelTimeout(f"model did not start answering within {settings.model_timeout_s:g}s") from None
    except Exception as exc:
        await store.save(thread)
        log.warning("provider error request_id=%s thread=%s: %s", request_id, thread_id, exc)
        raise ProviderError("model provider failed") from exc

    async def events() -> AsyncIterator[str]:
        try:
            yield sse_frame(first)
            async for item in turn:
                yield sse_frame(item)
        except asyncio.CancelledError:
            log.warning("stream cancelled by client request_id=%s thread=%s", request_id, thread_id)
            thread.append("run_failed", reason="client_disconnected")
            raise
        finally:
            await turn.aclose()
            await store.save(thread)

    headers = {"X-Prompt-Version": settings.prompt_version, "Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(events(), media_type="text/event-stream", headers=headers)
