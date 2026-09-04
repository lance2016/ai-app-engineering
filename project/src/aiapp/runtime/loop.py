"""The agent loop: settle pending tool calls, ask the model, act, repeat until the runtime says stop.

Combines lesson 06 (loop, budget, failure routing), lesson 07 (pause / resume
over an event thread, asking the human is a tool call) and lesson 08 (the
context window is assembled, not accumulated). Every step is appended to the
thread before the next one starts; the caller persists as events are yielded.

Like ``run_turn`` in M1, nothing is yielded until the first model chunk (or a
pause that needs no model call), so a timeout or provider error on the first
call still reaches the client as a real status code.
"""

import asyncio
import dataclasses
import logging
from collections.abc import AsyncIterator

from aiapp.adapters.base import Message, ModelAdapter, StreamChunk, ToolCall, ToolSpec, Usage
from aiapp.ops import telemetry as otel
from aiapp.runtime.budget import Budget, StopReason
from aiapp.runtime.context import ContextBuilder, estimate_tokens
from aiapp.runtime.registry import signature
from aiapp.runtime.runner import REQUEST_HUMAN_INPUT, NeedsConfirmation, RunContext, ToolRunner
from aiapp.runtime.skills import LOAD_SKILL, SkillLoader
from aiapp.runtime.turn import Delta
from aiapp.thread import Event, Thread, tool_calls_as_data

log = logging.getLogger("aiapp.runtime")

REQUEST_HUMAN_INPUT_SPEC = ToolSpec(
    REQUEST_HUMAN_INPUT,
    "Ask the user a question and wait for the answer. Use it when you cannot proceed without information only the user has.",
    {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
)


async def _next_chunk(stream: AsyncIterator[StreamChunk], timeout_s: float) -> StreamChunk:
    async with asyncio.timeout(timeout_s):
        return await anext(stream)


def _answered(thread: Thread, call_id: str) -> str | None:
    for e in reversed(thread.events):
        if e.type == "human_input" and e.data.get("tool_call_id") == call_id:
            return e.data.get("content", "")
    return None


async def run_agent(
    thread: Thread,
    model: ModelAdapter,
    runner: ToolRunner,
    *,
    ctx: RunContext,
    budget: Budget,
    context: ContextBuilder,
    skills: SkillLoader | None = None,
    timeout_s: float,
    user_content: str | None = None,
) -> AsyncIterator[Event | Delta]:
    buffered: list[Event] = []  # held back until the first model chunk so the caller can still answer with a status code
    streaming = False
    # The generator is resumed from different tasks (the request handler primes it, the response body drains it), so the
    # parent span travels explicitly instead of through the ambient context: contextvars do not cross tasks.
    root = otel.tracer().start_span("invoke_agent aiapp", attributes={otel.A_OPERATION: "invoke_agent", otel.A_AGENT_NAME: "aiapp", otel.A_CONVERSATION_ID: thread.thread_id, otel.A_TENANT: ctx.tenant_id, otel.A_THREAD: thread.thread_id})
    root_ctx = otel.trace.set_span_in_context(root)
    ctx = dataclasses.replace(ctx, otel_context=root_ctx)
    try:
        async for item in _run_agent(thread, model, runner, ctx=ctx, budget=budget, context=context, skills=skills, timeout_s=timeout_s, user_content=user_content, buffered=buffered, root_ctx=root_ctx):
            yield item
    except BaseException as exc:
        root.record_exception(exc)
        otel.mark_error(root, str(exc) or type(exc).__name__, type(exc).__name__)
        raise
    finally:
        last = thread.events[-1] if thread.events else None
        if last is not None and last.type in ("run_finished", "run_failed", "human_input_requested"):
            reason = last.data.get("reason", "finished" if last.type == "run_finished" else "paused")
            root.set_attribute(otel.A_STOP_REASON, str(reason))
            if last.type == "run_failed":
                otel.mark_error(root, str(reason))
            elif root.is_recording() and root.status.status_code == otel.StatusCode.UNSET:
                root.set_status(otel.Status(otel.StatusCode.OK))
        budget_now = budget.snapshot()
        root.set_attribute("aiapp.steps", budget_now["steps"])
        root.set_attribute("aiapp.tokens", budget_now["tokens"])
        root.end()


async def _run_agent(
    thread: Thread,
    model: ModelAdapter,
    runner: ToolRunner,
    *,
    ctx: RunContext,
    budget: Budget,
    context: ContextBuilder,
    skills: SkillLoader | None,
    timeout_s: float,
    user_content: str | None,
    buffered: list[Event],
    root_ctx=None,
) -> AsyncIterator[Event | Delta]:
    streaming = False

    def note(event: Event) -> list[Event | Delta]:
        if streaming:
            return [event]
        buffered.append(event)
        return []

    if user_content is not None:
        for item in note(thread.append("user_message", content=user_content)):
            yield item
    for item in note(thread.append("run_started", model=model.name, allowlist=sorted(ctx.allowlist))):
        yield item
    budget.start()
    specs = [*runner.registry.specs(ctx.allowlist), REQUEST_HUMAN_INPUT_SPEC]
    seen: set[str] = set()
    warned = False

    while True:
        # 1. settle everything the model already asked for but that has no result yet (also the resume path)
        for call in thread.pending_tool_calls():
            if call.name == REQUEST_HUMAN_INPUT:
                if _answered(thread, call.id) is None:
                    for item in note(thread.append("human_input_requested", tool_call_id=call.id, kind="question", question=call.arguments.get("question", ""))):
                        yield item
                    for item in buffered:
                        yield item
                    return
                continue  # the answer is already the tool result (Thread.to_messages)
            outcome = await runner.run(call, ctx, thread)
            if isinstance(outcome, NeedsConfirmation):
                for item in note(thread.append("human_input_requested", confirm_tool_call_id=call.id, kind="confirmation", tool=call.name, arguments=call.arguments)):
                    yield item
                for item in buffered:
                    yield item
                return
            for item in note(thread.append("tool_result", tool_call_id=call.id, name=call.name, content=outcome.message.content, is_error=outcome.message.is_error, **outcome.trace())):
                yield item
            if call.name == LOAD_SKILL and not outcome.message.is_error and skills is not None:
                for item in note(thread.append("skill_loaded", name=call.arguments.get("name"), tokens=estimate_tokens(outcome.message.content))):
                    yield item

        # 2. ask the model for the next step, streaming text as it arrives. One span per model call.
        messages = context.build(thread)
        chat_span = otel.tracer().start_span(f"chat {model.name}", context=root_ctx, attributes={otel.A_OPERATION: "chat", otel.A_PROVIDER: model.name, otel.A_REQUEST_MODEL: model.name})
        stream = model.stream(messages, tools=specs)
        try:
            chunk = await _next_chunk(stream, timeout_s)
        except TimeoutError as exc:
            otel.mark_error(chat_span, "model timeout before first chunk", "TimeoutError")
            chat_span.end()
            thread.append("run_failed", reason=StopReason.MODEL_TIMEOUT, stage="first_chunk", budget=budget.snapshot())
            raise
        except Exception as exc:
            chat_span.record_exception(exc)
            otel.mark_error(chat_span, str(exc), type(exc).__name__)
            chat_span.end()
            thread.append("run_failed", reason=StopReason.PROVIDER_ERROR, stage="first_chunk", detail=str(exc), budget=budget.snapshot())
            raise
        if not streaming:
            streaming = True
            for item in buffered:
                yield item
            buffered.clear()

        parts: list[str] = []
        usage: Usage | None = None
        tool_calls: tuple[ToolCall, ...] = ()
        while True:
            if chunk.delta:
                parts.append(chunk.delta)
                yield Delta(chunk.delta)
            if chunk.done:
                usage, tool_calls = chunk.usage, chunk.tool_calls
                break
            try:
                chunk = await _next_chunk(stream, timeout_s)
            except StopAsyncIteration:
                break
            except TimeoutError:
                otel.mark_error(chat_span, "model stalled mid-stream", "TimeoutError")
                chat_span.end()
                yield thread.append("run_failed", reason=StopReason.MODEL_TIMEOUT, stage="mid_stream", partial="".join(parts), budget=budget.snapshot())
                return
            except Exception as exc:
                chat_span.record_exception(exc)
                otel.mark_error(chat_span, str(exc), type(exc).__name__)
                chat_span.end()
                yield thread.append("run_failed", reason=StopReason.PROVIDER_ERROR, stage="mid_stream", detail=str(exc), budget=budget.snapshot())
                return

        content = "".join(parts)
        if usage:
            chat_span.set_attribute(otel.A_INPUT_TOKENS, usage.input_tokens)
            chat_span.set_attribute(otel.A_OUTPUT_TOKENS, usage.output_tokens)
        chat_span.set_attribute(otel.A_FINISH_REASONS, ["tool_calls" if tool_calls else "stop"])
        if not tool_calls and not content:
            chat_span.set_attribute("aiapp.empty_output", True)
            otel.mark_error(chat_span, "empty model output", "EmptyOutput")
        else:
            chat_span.set_status(otel.Status(otel.StatusCode.OK))
        chat_span.end()
        yield thread.append(
            "assistant_message", content=content, tool_calls=tool_calls_as_data(tool_calls), context=context.report.as_dict(),
            usage=_usage_dict(usage), model=getattr(model, "last_served_by", None) and f"{model.name}:{model.last_served_by}" or model.name,
        )
        spent = (usage.input_tokens + usage.output_tokens) if usage else estimate_tokens(content)
        exhausted = budget.charge(tokens=spent)

        # 3. stop conditions belong to the runtime
        if not tool_calls:
            yield thread.append("run_finished", answer=content, usage=_usage_dict(usage), budget=budget.snapshot())
            return
        if exhausted:
            yield thread.append("run_failed", reason=exhausted, budget=budget.snapshot(), pending=[c.name for c in tool_calls])
            return

        # 4. off-track: the same call again gets one warning, then the run escalates to a person
        for call in tool_calls:
            sig = signature(call)
            if sig in seen and call.name != REQUEST_HUMAN_INPUT:
                if warned:
                    yield thread.append("run_failed", reason=StopReason.OFF_TRACK, repeated=call.name, budget=budget.snapshot())
                    return
                warned = True
                yield thread.append("tool_result", tool_call_id=call.id, name=call.name, is_error=True, route="off_track_warning", duration_ms=0, attempts=0,
                                    content="you already called this with the same arguments; use the previous result or try something else")
            seen.add(sig)


def _usage_dict(usage: Usage | None) -> dict[str, int] | None:
    return {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens} if usage else None


def tool_messages_for(thread: Thread) -> list[Message]:
    """Convenience for tests: the tool results the model would see."""
    return [m for m in thread.to_messages() if m.role == "tool"]
