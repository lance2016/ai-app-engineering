"""Threads: create one, read it back, send a message, answer the agent's question or approve a side effect.

The run itself is ``aiapp.runtime.run_agent``. This module owns everything
around it: per-step checkpoints (M2), the per-thread run lock and idempotent
replays (M2), the request-level tool allowlist and the resume path after a
human answers (M3).
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
from aiapp.api.deps import Tenant, get_kv, get_model, get_runner, get_settings, get_skills, get_store, get_system_prompt, get_tenant
from aiapp.api.errors import Conflict, InvalidRequest, ModelTimeout, NotFound, ProviderError, request_id_of
from aiapp.api.schemas import CreateThreadRequest, HumanInputRequest, MessageRequest, ThreadView
from aiapp.config import Settings
from aiapp.runtime import Budget, ContextBuilder, Delta, RunContext, SkillLoader, ToolRunner, run_agent
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


def _allowlist(settings: Settings, runner: ToolRunner, requested: list[str] | None) -> frozenset[str]:
    """Server policy first, then the request may narrow it. It can never widen it."""
    allowed = settings.tool_allowlist if settings.tool_allowlist is not None else runner.registry.names()
    if requested is None:
        return frozenset(allowed)
    unknown = set(requested) - runner.registry.names()
    if unknown:
        raise InvalidRequest(f"allowed_tools: unknown tools {sorted(unknown)}")
    return frozenset(requested) & frozenset(allowed)


async def _run_and_stream(
    *,
    request: Request,
    thread: Thread,
    tenant: Tenant,
    store: ThreadStore,
    kv: KeyValueStore,
    model: ModelAdapter,
    runner: ToolRunner,
    skills: SkillLoader,
    settings: Settings,
    system_prompt: str,
    allowlist: frozenset[str],
    user_content: str | None,
    idempotency_key: str | None,
    prelude: tuple[str, dict] | None = None,
) -> StreamingResponse:
    """Run the agent and stream its events. ``prelude`` is an event to record and stream before the run (the human's answer)."""
    thread_id, request_id = thread.thread_id, request_id_of(request)

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

    persisted = from_seq = len(thread.events)
    prelude_event = thread.append(prelude[0], **prelude[1]) if prelude else None
    ctx = RunContext(tenant_id=tenant.id, thread_id=thread_id, allowlist=allowlist)
    budget = Budget(max_steps=settings.max_steps, max_tokens=settings.max_tokens, max_seconds=settings.max_seconds)
    context = ContextBuilder(system_prompt, budget_tokens=settings.context_budget_tokens, skill_catalog=skills.catalog())
    run = run_agent(thread, model, runner, ctx=ctx, budget=budget, context=context, skills=skills, timeout_s=settings.model_timeout_s, user_content=user_content)

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

    # 3. Reach the first event before committing to a 200: a model timeout or outage here is a real status code.
    try:
        first = await anext(run)
    except StopAsyncIteration:
        first = None
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
            if prelude_event is not None:
                yield sse_frame(prelude_event)
            if first is not None:
                yield sse_frame(first)
                await checkpoint()
                async for item in run:
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
            await run.aclose()
            try:
                await checkpoint()
            except SeqConflict:
                pass
            await finish(record=completed)

    return _sse_response(events(), settings)


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    body: MessageRequest,
    request: Request,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
    kv: Annotated[KeyValueStore, Depends(get_kv)],
    model: Annotated[ModelAdapter, Depends(get_model)],
    runner: Annotated[ToolRunner, Depends(get_runner)],
    skills: Annotated[SkillLoader, Depends(get_skills)],
    settings: Annotated[Settings, Depends(get_settings)],
    system_prompt: Annotated[str, Depends(get_system_prompt)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    thread = await _load(store, thread_id, tenant)
    if thread.status() == "paused":
        raise Conflict("the agent is waiting for human input; answer it via /human-input first")
    return await _run_and_stream(
        request=request, thread=thread, tenant=tenant, store=store, kv=kv, model=model, runner=runner, skills=skills,
        settings=settings, system_prompt=system_prompt, allowlist=_allowlist(settings, runner, body.allowed_tools),
        user_content=body.content, idempotency_key=idempotency_key,
    )


@router.post("/{thread_id}/human-input")
async def human_input(
    thread_id: str,
    body: HumanInputRequest,
    request: Request,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    store: Annotated[ThreadStore, Depends(get_store)],
    kv: Annotated[KeyValueStore, Depends(get_kv)],
    model: Annotated[ModelAdapter, Depends(get_model)],
    runner: Annotated[ToolRunner, Depends(get_runner)],
    skills: Annotated[SkillLoader, Depends(get_skills)],
    settings: Annotated[Settings, Depends(get_settings)],
    system_prompt: Annotated[str, Depends(get_system_prompt)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> StreamingResponse:
    """Answer the agent's question or decide on a confirmation, then resume the run from the checkpoint."""
    thread = await _load(store, thread_id, tenant)
    if thread.status() != "paused":
        raise Conflict("the agent is not waiting for human input")
    pending = next(e for e in reversed(thread.events) if e.type == "human_input_requested")
    if pending.data.get("kind") == "confirmation":
        if body.confirm_tool_call_id != pending.data["confirm_tool_call_id"] or body.approved is None:
            raise InvalidRequest(f"expected confirm_tool_call_id={pending.data['confirm_tool_call_id']!r} and approved=true|false")
        prelude = ("human_input", {"confirm_tool_call_id": body.confirm_tool_call_id, "approved": body.approved})
    else:
        if body.tool_call_id != pending.data["tool_call_id"] or body.content is None:
            raise InvalidRequest(f"expected tool_call_id={pending.data['tool_call_id']!r} and content")
        prelude = ("human_input", {"tool_call_id": body.tool_call_id, "content": body.content})
    allowlist = frozenset(next(e for e in reversed(thread.events) if e.type == "run_started").data.get("allowlist", []))
    return await _run_and_stream(
        request=request, thread=thread, tenant=tenant, store=store, kv=kv, model=model, runner=runner, skills=skills,
        settings=settings, system_prompt=system_prompt, allowlist=allowlist, user_content=None, idempotency_key=idempotency_key,
        prelude=prelude,
    )
