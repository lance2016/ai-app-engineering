"""ToolRunner guards, one per test. The seven routes the M3 README lists, plus the replay path."""

import pytest

from aiapp import Thread, ToolCall
from aiapp.runtime import NeedsConfirmation, ToolFailed, ToolRegistry, ToolRunner
from aiapp.runtime.runner import idempotency_key
from aiapp.adapters.base import ToolSpec
from aiapp.runtime.registry import Tool
from tests.project.m3.conftest import ctx_for

pytestmark = pytest.mark.anyio


def call(name: str, **args) -> ToolCall:
    return ToolCall(id=f"c_{name}", name=name, arguments=args)


async def test_unknown_tool_is_an_error_result_not_an_exception(runner: ToolRunner) -> None:
    thread = Thread()
    out = await runner.run(call("delete_user_data", user_id="u1"), ctx_for(thread), thread)
    assert out.route == "unknown_tool" and out.message.is_error and "unknown tool" in out.message.content


async def test_registered_but_not_allowed_here(runner: ToolRunner) -> None:
    thread = Thread()
    out = await runner.run(call("search_docs", query="refund"), ctx_for(thread, {"read_doc"}), thread)
    assert out.route == "not_allowed" and out.message.is_error


async def test_invalid_arguments_name_the_field(runner: ToolRunner) -> None:
    thread = Thread()
    out = await runner.run(call("search_docs", query="refund", limit=99), ctx_for(thread), thread)
    assert out.route == "invalid_input" and "limit" in out.message.content
    out = await runner.run(call("delete_doc", doc_id="doc_refunds", reason="because"), ctx_for(thread), thread)
    assert out.route == "invalid_input" and "reason" in out.message.content


async def test_side_effect_needs_confirmation_then_runs_once(runner: ToolRunner, docs) -> None:
    thread = Thread()
    c = call("delete_doc", doc_id="doc_returns_draft", reason="draft")
    assert isinstance(await runner.run(c, ctx_for(thread), thread), NeedsConfirmation)
    assert docs.deleted == [], "nothing runs on the model's word alone"

    thread.append("human_input", confirm_tool_call_id=c.id, approved=True)
    out = await runner.run(c, ctx_for(thread), thread)
    assert out.route == "ok" and docs.deleted == ["doc_returns_draft"]

    again = await runner.run(c, ctx_for(thread), thread)  # a retry of the same call, e.g. after a crash before the result was recorded
    assert again.route == "replayed" and again.message.content == out.message.content
    assert docs.deleted == ["doc_returns_draft"], "one side effect, however many attempts"


async def test_declined_side_effect_is_reported_to_the_model(runner: ToolRunner, docs) -> None:
    thread = Thread()
    c = call("delete_doc", doc_id="doc_refunds")
    thread.append("human_input", confirm_tool_call_id=c.id, approved=False)
    out = await runner.run(c, ctx_for(thread), thread)
    assert out.route == "declined" and out.message.is_error and "declined" in out.message.content
    assert "doc_refunds" in docs.docs


async def test_crash_between_execute_and_record_never_re_executes(runner: ToolRunner, kv, docs) -> None:
    """Failure injection: the key was claimed, the process died before recording. The retry must not run the tool again."""
    thread = Thread()
    c = call("delete_doc", doc_id="doc_refunds")
    thread.append("human_input", confirm_tool_call_id=c.id, approved=True)
    await kv.claim(idempotency_key(c, ctx_for(thread)), "running", 60)  # what a dead process leaves behind
    out = await runner.run(c, ctx_for(thread), thread)
    assert out.route == "in_progress" and out.message.is_error
    assert docs.deleted == []


async def test_transient_errors_are_retried_with_a_cap(runner: ToolRunner, docs) -> None:
    thread = Thread()
    docs.fail_next_searches = 1
    out = await runner.run(call("search_docs", query="refund"), ctx_for(thread), thread)
    assert out.route == "ok" and out.attempts == 2 and "doc_refunds" in out.message.content

    docs.fail_next_searches = 10
    out = await runner.run(ToolCall(id="c2", name="search_docs", arguments={"query": "shipping"}), ctx_for(thread), thread)
    assert out.route == "transient_exhausted" and out.attempts == 3 and out.message.is_error


async def test_tool_failure_is_recorded_and_replayed_but_a_crash_is_not(kv) -> None:
    reg = ToolRegistry()
    calls = {"failing": 0, "crashing": 0}

    def failing(a):
        calls["failing"] += 1
        raise ToolFailed("account is frozen")

    def crashing(a):
        calls["crashing"] += 1
        raise KeyError("bug")

    reg.register(Tool(ToolSpec("failing", "x", {"type": "object", "properties": {}}), failing))
    reg.register(Tool(ToolSpec("crashing", "x", {"type": "object", "properties": {}}), crashing))
    runner = ToolRunner(reg, kv)
    thread = Thread()
    ctx = ctx_for(thread, {"failing", "crashing"})

    first, second = await runner.run(call("failing"), ctx, thread), await runner.run(call("failing"), ctx, thread)
    assert first.route == "failed" and second.route == "replayed" and calls["failing"] == 1

    first, second = await runner.run(call("crashing"), ctx, thread), await runner.run(call("crashing"), ctx, thread)
    assert first.route == "failed" and "KeyError" in first.message.content
    assert second.route == "failed" and calls["crashing"] == 2, "a bug is not a result; the key is released so a fixed tool can run"


async def test_trace_fields_are_present(runner: ToolRunner) -> None:
    thread = Thread()
    out = await runner.run(call("read_doc", doc_id="doc_refunds"), ctx_for(thread), thread)
    assert set(out.trace()) == {"duration_ms", "attempts", "route"} and out.trace()["attempts"] == 1
