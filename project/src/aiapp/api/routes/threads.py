"""Threads: create one, read it back, send a message and watch the run as server-sent events.

M2 additions: every event is persisted as soon as it exists (checkpoint per step),
a per-thread run lock rejects a second message while a run is in progress
(the *reject* double-texting strategy from lesson 07), and an ``Idempotency-Key``
header makes a retried request replay the first run's events instead of
calling the model again.
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse

from aiapp.adapters.base import ModelAdapter
from aiapp.api.deps import Tenant, get_kv, get_model, get_settings, get_store, get_system_prompt, get_tenant
from aiapp.api.errors import Conflict, ModelTimeout, NotFound, ProviderError, request_id_of
from aiapp.api.schemas import CreateThreadRequest, MessageRequest, ThreadView
from aiapp.config import Settings
from aiapp.runtime import Delta, run_turn
from aiapp.storage.base import KeyValueStore, SeqConflict, ThreadNotFound, ThreadStore, flush
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
        await flush(store, thread, 0)
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


def _sse_response(body: AsyncIterator[str], settings: Settings, *, replayed: bool = False) -> StreamingResponse:
    headers = {"X-Prompt-Version": settings.prompt_version, "Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    if replayed:
        headers["X-Idempotent-Replay"] = "true"
    return StreamingResponse(body, media_type="text/event-stream", headers=headers)


async def _replay(thread: Thread, from_seq: int, to_seq: int) -> AsyncIterator[str]:
    for event in thread.events[from_seq:to_seq]:
        yield sse_frame(event)


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    body: MessageRequest,
    request: Request,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
    kv: Annotated[KeyValueStore, Depends(get_kv)],
    model: Annotated[ModelAdapter, Depends(get_model)],
    settings: Annotated[Settings, Depends(get_settings)],
    system_prompt: Annotated[str, Depends(get_system_prompt)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    thread = await _load(store, thread_id, tenant)
    request_id = request_id_of(request)

    # 1. Idempotency: a retried request replays the events the first one produced. No second model call.
    idem_key = f"idem:{tenant.id}:{thread_id}:{idempotency_key}" if idempotency_key else None
    if idem_key:
        recorded = await kv.get(idem_key)
        if recorded and recorded != "claimed":
            span = json.loads(recorded)
            log.info("idempotent replay request_id=%s thread=%s seq=%s..%s", request_id, thread_id, span["from_seq"], span["to_seq"])
            return _sse_response(_replay(thread, span["from_seq"], span["to_seq"]), settings, replayed=True)
        if not await kv.claim(idem_key, "claimed", settings.idempotency_ttl_s):
            raise Conflict("a request with this Idempotency-Key is still in progress")

    # 2. Run lock: one run per thread at a time. The second message is rejected, not queued (lesson 07: reject).
    lock_key, lock_token = f"run:{thread_id}", uuid.uuid4().hex
    if not await kv.claim(lock_key, lock_token, settings.run_lock_ttl_s):
        if idem_key:
            await kv.release(idem_key, "claimed")
        raise Conflict("a run is already in progress on this thread")

    persisted = len(thread.events)
    turn = run_turn(thread, model, system_prompt=system_prompt, user_content=body.content, timeout_s=settings.model_timeout_s)

    async def checkpoint() -> None:
        nonlocal persisted
        persisted = await flush(store, thread, persisted)

    async def finish(*, record: bool) -> None:
        await kv.release(lock_key, lock_token)
        if idem_key:
            if record:
                await kv.set(idem_key, json.dumps({"from_seq": from_seq, "to_seq": persisted}), settings.idempotency_ttl_s)
            else:
                await kv.release(idem_key, "claimed")

    from_seq = persisted
    # 3. Reach the model's first chunk before committing to a 200: a timeout or outage here is a real status code.
    try:
        first = await anext(turn)
    except TimeoutError:
        await checkpoint()
        await finish(record=False)
        raise ModelTimeout(f"model did not start answering within {settings.model_timeout_s:g}s") from None
    except Exception as exc:
        await checkpoint()
        await finish(record=False)
        log.warning("provider error request_id=%s thread=%s: %s", request_id, thread_id, exc)
        raise ProviderError("model provider failed") from exc

    async def events() -> AsyncIterator[str]:
        completed = False
        try:
            yield sse_frame(first)
            await checkpoint()
            async for item in turn:
                yield sse_frame(item)
                if isinstance(item, Event):
                    await checkpoint()  # every step is durable before the next one starts
            completed = True
        except asyncio.CancelledError:
            log.warning("stream cancelled by client request_id=%s thread=%s", request_id, thread_id)
            thread.append("run_failed", reason="client_disconnected")
            raise
        except SeqConflict as exc:
            log.error("lost the write race request_id=%s thread=%s: %s", request_id, thread_id, exc)
            yield sse_frame(Event(type="run_failed", data={"reason": "seq_conflict"}))
        finally:
            await turn.aclose()
            try:
                await checkpoint()
            except SeqConflict:
                pass
            await finish(record=completed)

    return _sse_response(events(), settings)
