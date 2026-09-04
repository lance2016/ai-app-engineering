"""ToolRunner: everything that happens between "the model asked for a tool" and "here is the result".

validate -> authorize -> confirm (pause if a side effect is not yet approved)
-> execute with an idempotency key and bounded retries -> record the trace.

Every failure is classified and routed by code (lesson 06): transient errors are
retried, invalid input goes back to the model as an error result, a side effect
without approval does not run. Nothing here asks the model how to recover.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

from aiapp.adapters.base import Message, ToolCall
from aiapp.runtime.errors import ToolFailed, TransientToolError
from aiapp.runtime.registry import ToolRegistry, signature
from aiapp.storage.base import KeyValueStore
from aiapp.thread import Thread

log = logging.getLogger("aiapp.runtime")

REQUEST_HUMAN_INPUT = "request_human_input"  # reserved: handled by the loop, never by the runner


@dataclass(frozen=True)
class RunContext:
    tenant_id: str
    thread_id: str
    allowlist: frozenset[str]


@dataclass(frozen=True)
class NeedsConfirmation:
    """The tool has side effects and nobody has approved this exact call yet."""

    call: ToolCall


@dataclass(frozen=True)
class ToolOutcome:
    message: Message
    duration_ms: int
    attempts: int
    route: str  # ok | unknown_tool | not_allowed | invalid_input | declined | replayed | in_progress | transient_exhausted | failed

    def trace(self) -> dict[str, Any]:
        return {"duration_ms": self.duration_ms, "attempts": self.attempts, "route": self.route}


def idempotency_key(call: ToolCall, ctx: RunContext) -> str:
    """Derived from the call itself (lesson 05): the model never has to know about it."""
    return "tool:" + hashlib.sha256(f"{ctx.tenant_id}:{ctx.thread_id}:{call.id}:{signature(call)}".encode()).hexdigest()[:24]


def confirmation_for(thread: Thread, call_id: str) -> bool | None:
    """True approved, False declined, None nobody has answered yet."""
    for e in reversed(thread.events):
        if e.type == "human_input" and e.data.get("confirm_tool_call_id") == call_id:
            return bool(e.data.get("approved"))
    return None


class ToolRunner:
    def __init__(
        self,
        registry: ToolRegistry,
        kv: KeyValueStore,
        *,
        max_transient_retries: int = 2,
        retry_base_delay_s: float = 0.05,
        result_ttl_s: int = 86_400,
    ):
        self.registry = registry
        self._kv = kv
        self.max_transient_retries = max_transient_retries
        self.retry_base_delay_s = retry_base_delay_s
        self.result_ttl_s = result_ttl_s

    async def run(self, call: ToolCall, ctx: RunContext, thread: Thread) -> ToolOutcome | NeedsConfirmation:
        started = time.monotonic()

        def outcome(content: str, *, route: str, is_error: bool, attempts: int = 0) -> ToolOutcome:
            message = Message(role="tool", tool_call_id=call.id, content=content, is_error=is_error)
            return ToolOutcome(message, duration_ms=int((time.monotonic() - started) * 1000), attempts=attempts, route=route)

        # 1. validate the name
        tool = self.registry.get(call.name)
        if tool is None:
            return outcome(f"unknown tool: {call.name}", route="unknown_tool", is_error=True)
        # 2. authorize: the request's allowlist, not the registry, decides
        if call.name not in ctx.allowlist:
            return outcome(f"tool not allowed here: {call.name}", route="not_allowed", is_error=True)
        # 3. validate the arguments; a schema error is feedback for the model, not an exception
        try:
            arguments = tool.validate(call.arguments)
        except ValueError as exc:
            return outcome(str(exc), route="invalid_input", is_error=True)
        # 4. side effects run only on an explicit yes recorded in the thread
        if tool.has_side_effects:
            decision = confirmation_for(thread, call.id)
            if decision is None:
                return NeedsConfirmation(call)
            if decision is False:
                return outcome("user declined; nothing was changed", route="declined", is_error=True)
        # 5. idempotency: the same call never produces the side effect twice, whatever the model calls it
        key = idempotency_key(call, ctx)
        if not await self._kv.claim(key, "running", self.result_ttl_s):
            recorded = await self._kv.get(key)
            if recorded and recorded != "running":
                stored = json.loads(recorded)
                log.info("tool replay thread=%s call=%s", ctx.thread_id, call.id)
                return outcome(stored["content"], route="replayed", is_error=stored["is_error"])
            return outcome(f"{call.name} is already executing for this call", route="in_progress", is_error=True)
        # 6. execute with bounded retries; classify what comes back
        attempts = 0
        try:
            for attempt in range(1, self.max_transient_retries + 2):
                attempts = attempt
                try:
                    content = await tool.execute(arguments)
                except TransientToolError as exc:
                    log.warning("transient tool error thread=%s tool=%s attempt=%s: %s", ctx.thread_id, call.name, attempt, exc)
                    if attempt > self.max_transient_retries:
                        await self._kv.release(key, "running")
                        return outcome(f"{call.name} unavailable after {attempts} attempts: {exc}", route="transient_exhausted", is_error=True, attempts=attempts)
                    await asyncio.sleep(self.retry_base_delay_s * 2 ** (attempt - 1))
                    continue
                except ValueError as exc:  # the tool itself rejected the input: feedback, no retry
                    await self._kv.release(key, "running")
                    return outcome(str(exc), route="invalid_input", is_error=True, attempts=attempts)
                except ToolFailed as exc:
                    await self._record(key, str(exc), is_error=True)
                    return outcome(str(exc), route="failed", is_error=True, attempts=attempts)
                await self._record(key, content, is_error=False)
                return outcome(content, route="ok", is_error=False, attempts=attempts)
        except Exception as exc:  # a bug in the tool must not take the run down
            log.exception("tool crashed thread=%s tool=%s", ctx.thread_id, call.name)
            await self._kv.release(key, "running")
            return outcome(f"{call.name} failed: {type(exc).__name__}", route="failed", is_error=True, attempts=attempts)
        raise AssertionError("unreachable")

    async def _record(self, key: str, content: str, *, is_error: bool) -> None:
        await self._kv.set(key, json.dumps({"content": content, "is_error": is_error}, ensure_ascii=False), self.result_ttl_s)
