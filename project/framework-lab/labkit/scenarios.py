"""Scenarios every implementation must pass. Each returns nothing and raises AssertionError with a precise message.

A scenario receives a ``factory(world) -> LabRuntime`` so it can simulate a process
restart by closing one runtime and building another over the same LabWorld.
"""

from collections.abc import Awaitable, Callable
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, tool_call_response
from aiapp.tools.demo import DocStore
from labkit.protocol import LabRuntime, LabWorld, RunOutcome

Factory = Callable[[LabWorld], Awaitable[LabRuntime]]


def world(workdir: Path, script: list[ModelResponse]) -> LabWorld:
    return LabWorld(workdir=workdir, model=FakeAdapter(script=script), docs=DocStore())


async def read_only_happy_path(factory: Factory, workdir: Path) -> RunOutcome:
    w = world(workdir, [
        tool_call_response("search_docs", {"query": "refund"}, call_id="c1"),
        tool_call_response("read_doc", {"doc_id": "doc_refunds"}, call_id="c2"),
        ModelResponse(content="Full refund within 30 days with a receipt."),
    ])
    rt = await factory(w)
    try:
        out = await rt.start("t-happy", "What is the refund policy?")
    finally:
        await rt.close()
    assert out.status == "finished", f"status {out.status}: {out.detail}"
    assert out.tools_ran() == ["search_docs", "read_doc"], out.tools_ran()
    assert out.answer and "30 days" in out.answer, out.answer
    types = [e.type for e in out.events]
    assert types[0] == "user_message" and types[-1] == "run_finished", types
    assert w.docs.deleted == []
    return out


async def confirmation_pause_restart_resume(factory: Factory, workdir: Path) -> tuple[RunOutcome, RunOutcome]:
    w = world(workdir, [
        tool_call_response("delete_doc", {"doc_id": "doc_returns_draft", "reason": "draft"}, call_id="c1"),
        ModelResponse(content="Deleted the draft."),
    ])
    rt = await factory(w)
    first = await rt.start("t-confirm", "Delete the returns draft.")
    await rt.close()  # the process dies here
    assert first.status == "paused", f"status {first.status}: {first.detail}"
    assert first.pending and first.pending["kind"] == "confirmation" and first.pending["tool"] == "delete_doc", first.pending
    assert w.docs.deleted == [], "nothing runs on the model's word alone"

    rt2 = await factory(w)  # a new process over the same durable state
    try:
        second = await rt2.resume("t-confirm", approved=True)
    finally:
        await rt2.close()
    assert second.status == "finished", f"status {second.status}: {second.detail}"
    assert w.docs.deleted == ["doc_returns_draft"], f"side effect ran {len(w.docs.deleted)} times"
    assert second.answer and "Deleted" in second.answer
    return first, second


async def confirmation_declined(factory: Factory, workdir: Path) -> RunOutcome:
    w = world(workdir, [
        tool_call_response("delete_doc", {"doc_id": "doc_refunds"}, call_id="c1"),
        ModelResponse(content="Okay, I left it in place."),
    ])
    rt = await factory(w)
    try:
        first = await rt.start("t-decline", "Delete the refund doc.")
        assert first.status == "paused"
        out = await rt.resume("t-decline", approved=False)
    finally:
        await rt.close()
    assert out.status == "finished", f"status {out.status}: {out.detail}"
    assert w.docs.deleted == [] and "doc_refunds" in w.docs.docs
    assert any(e.data.get("is_error") for e in out.tool_results()), "the model must be told the action was declined"
    return out


async def question_round_trip(factory: Factory, workdir: Path) -> tuple[RunOutcome, RunOutcome]:
    w = world(workdir, [
        tool_call_response("request_human_input", {"question": "Refunds or shipping?"}, call_id="q1"),
        ModelResponse(content="Shipping is free over 50."),
    ])
    rt = await factory(w)
    try:
        first = await rt.start("t-question", "What does the doc say?")
        assert first.status == "paused" and first.pending and first.pending["kind"] == "question", (first.status, first.pending, first.detail)
        second = await rt.resume("t-question", answer="shipping")
    finally:
        await rt.close()
    assert second.status == "finished" and second.answer and "Shipping" in second.answer, (second.status, second.detail)
    return first, second


async def double_texting_is_rejected_while_paused(factory: Factory, workdir: Path) -> RunOutcome:
    w = world(workdir, [
        tool_call_response("delete_doc", {"doc_id": "doc_refunds"}, call_id="c1"),
        ModelResponse(content="unreachable"),
    ])
    rt = await factory(w)
    try:
        assert (await rt.start("t-double", "Delete the refund doc.")).status == "paused"
        second = await rt.start("t-double", "Hurry up!")
    finally:
        await rt.close()
    assert second.status == "rejected", f"a new message while waiting for a human must be rejected, got {second.status}"
    assert w.docs.deleted == []
    return second


async def history_survives_restart(factory: Factory, workdir: Path) -> list:
    w = world(workdir, [ModelResponse(content="Hello there.")])
    rt = await factory(w)
    await rt.start("t-history", "hi")
    await rt.close()
    rt2 = await factory(w)
    try:
        events = await rt2.history("t-history")
    finally:
        await rt2.close()
    types = [e.type for e in events]
    assert "user_message" in types and "assistant_message" in types, types
    return events


async def step_limit_stops_an_endless_model(factory: Factory, workdir: Path) -> RunOutcome:
    w = world(workdir, [tool_call_response("search_docs", {"query": f"q{i}"}, call_id=f"c{i}") for i in range(40)])
    rt = await factory(w)
    try:
        out = await rt.start("t-endless", "Search forever.")
    finally:
        await rt.close()
    assert out.status == "failed", f"an endless loop must end as failed, got {out.status}"
    assert len(out.tools_ran()) < 40, "the runtime, not the model, decided when to stop"
    return out


async def unknown_tool_does_not_crash(factory: Factory, workdir: Path) -> RunOutcome:
    w = world(workdir, [tool_call_response("drop_table", {"name": "users"}, call_id="c1"), ModelResponse(content="I do not have that tool.")])
    rt = await factory(w)
    try:
        out = await rt.start("t-unknown", "Wipe the users table.")
    finally:
        await rt.close()
    assert out.status in ("finished", "failed"), out.status
    assert w.docs.deleted == []
    return out


SCENARIOS = {
    "read_only_happy_path": read_only_happy_path,
    "confirmation_pause_restart_resume": confirmation_pause_restart_resume,
    "confirmation_declined": confirmation_declined,
    "question_round_trip": question_round_trip,
    "double_texting_is_rejected_while_paused": double_texting_is_rejected_while_paused,
    "history_survives_restart": history_survives_restart,
    "step_limit_stops_an_endless_model": step_limit_stops_an_endless_model,
    "unknown_tool_does_not_crash": unknown_tool_does_not_crash,
}
