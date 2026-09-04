"""run_agent: stop conditions, pause / resume, failure routing, skills and context assembly."""

import pytest

from aiapp import FakeAdapter, ModelResponse, Thread, tool_call_response
from aiapp.runtime import Budget, StopReason
from aiapp.runtime.registry import Tool
from aiapp.adapters.base import ToolSpec
from tests.project.m3.conftest import drive, types

pytestmark = pytest.mark.anyio


async def test_happy_path_search_read_answer(runner) -> None:
    thread = Thread()
    script = [
        tool_call_response("search_docs", {"query": "refund"}, call_id="c1"),
        tool_call_response("read_doc", {"doc_id": "doc_refunds"}, call_id="c2"),
        ModelResponse(content="Full refund within 30 days with a receipt."),
    ]
    events, text, model = await drive(thread, script, runner, user_content="What is the refund policy?")
    assert types(events) == ["user_message", "run_started", "assistant_message", "tool_result", "assistant_message", "tool_result", "assistant_message", "run_finished"]
    assert text == "Full refund within 30 days with a receipt."
    tool_results = [e for e in events if e.type == "tool_result"]
    assert all(e.data["route"] == "ok" and "duration_ms" in e.data and e.data["attempts"] == 1 for e in tool_results)
    assert events[-1].data["budget"]["steps"] == 3
    assert thread.status() == "finished"
    # the model saw system prompt, then the history, with tool results as tool messages
    assert [m.role for m in model.calls[2]] == ["system", "user", "assistant", "tool", "assistant", "tool"]


async def test_side_effect_pauses_for_confirmation_then_resumes(runner, docs) -> None:
    thread = Thread()
    script = [tool_call_response("delete_doc", {"doc_id": "doc_returns_draft", "reason": "draft"}, call_id="c1"), ModelResponse(content="Deleted the draft.")]
    events, _, model = await drive(thread, script, runner, user_content="remove the draft")
    assert types(events)[-1] == "human_input_requested"
    assert events[-1].data == {"confirm_tool_call_id": "c1", "kind": "confirmation", "tool": "delete_doc", "arguments": {"doc_id": "doc_returns_draft", "reason": "draft"}}
    assert thread.status() == "paused" and docs.deleted == []

    thread.append("human_input", confirm_tool_call_id="c1", approved=True)
    events, text, _ = await drive(thread, [], runner, user_content=None, model=model)  # "another process": same script continues
    assert types(events) == ["run_started", "tool_result", "assistant_message", "run_finished"]
    assert docs.deleted == ["doc_returns_draft"] and text == "Deleted the draft."


async def test_declined_confirmation_lets_the_model_answer_gracefully(runner, docs) -> None:
    thread = Thread()
    script = [tool_call_response("delete_doc", {"doc_id": "doc_refunds"}, call_id="c1"), ModelResponse(content="Okay, I left it in place.")]
    _, _, model = await drive(thread, script, runner, user_content="delete the refund doc")
    thread.append("human_input", confirm_tool_call_id="c1", approved=False)
    events, text, _ = await drive(thread, [], runner, user_content=None, model=model)
    assert events[1].type == "tool_result" and events[1].data["route"] == "declined"
    assert text == "Okay, I left it in place." and "doc_refunds" in docs.docs


async def test_asking_the_user_is_a_tool_call(runner) -> None:
    thread = Thread()
    script = [tool_call_response("request_human_input", {"question": "Which document, refunds or shipping?"}, call_id="q1"), ModelResponse(content="Shipping is free over 50.")]
    events, _, model = await drive(thread, script, runner, user_content="what does the doc say?")
    assert events[-1].type == "human_input_requested" and events[-1].data["kind"] == "question" and events[-1].data["tool_call_id"] == "q1"
    thread.append("human_input", tool_call_id="q1", content="shipping")
    events, text, _ = await drive(thread, [], runner, user_content=None, model=model)
    assert types(events) == ["run_started", "assistant_message", "run_finished"]
    answered = [m for m in model.calls[-1] if m.role == "tool"]
    assert answered[-1].tool_call_id == "q1" and answered[-1].content == "shipping", "the answer is the tool result"


async def test_step_limit_stops_an_endless_model(runner) -> None:
    thread = Thread()
    script = [tool_call_response("search_docs", {"query": f"q{i}"}) for i in range(50)]
    events, _, _ = await drive(thread, script, runner, budget=Budget(max_steps=3))
    assert events[-1].type == "run_failed" and events[-1].data["reason"] == StopReason.STEP_LIMIT
    assert events[-1].data["budget"]["steps"] == 3 and thread.status() == "failed"


async def test_token_budget_stops_a_verbose_model(runner) -> None:
    thread = Thread()
    script = [tool_call_response("search_docs", {"query": "x" * 4000}), tool_call_response("search_docs", {"query": "y" * 4000}), ModelResponse(content="never")]
    events, _, _ = await drive(thread, script, runner, budget=Budget(max_steps=10, max_tokens=10))
    assert events[-1].data["reason"] == StopReason.TOKEN_BUDGET


async def test_repeating_the_same_call_gets_one_warning_then_escalates(runner) -> None:
    thread = Thread()
    same = lambda: tool_call_response("read_doc", {"doc_id": "doc_refunds"}, call_id="c")  # noqa: E731
    events, _, _ = await drive(thread, [same(), same(), same(), ModelResponse(content="unreachable")], runner)
    routes = [e.data.get("route") for e in events if e.type == "tool_result"]
    assert routes == ["ok", "off_track_warning"]
    assert events[-1].type == "run_failed" and events[-1].data["reason"] == StopReason.OFF_TRACK


async def test_first_chunk_timeout_raises_and_records(runner) -> None:
    from aiapp.adapters.inject import SlowAdapter

    thread = Thread()
    with pytest.raises(TimeoutError):
        await drive(thread, [], runner, model=SlowAdapter(FakeAdapter(), delay_s=5), timeout_s=0.05)
    assert thread.status() == "failed" and thread.events[-1].data["stage"] == "first_chunk"


async def test_skill_is_loaded_on_demand_and_traced(runner, skills) -> None:
    thread = Thread()
    script = [
        tool_call_response("load_skill", {"name": "expense-report"}, call_id="s1"),
        tool_call_response("read_skill_reference", {"skill": "expense-report", "path": "references/policy.md"}, call_id="s2"),
        ModelResponse(content="Hotel 650 is over the 600 limit."),
    ]
    events, _, model = await drive(thread, script, runner, skills=skills, user_content="Review: hotel 650, dinner 45.")
    assert model.calls[0][0].content.endswith(skills.catalog()), "level 1: the catalog is in the system prompt"
    assert "Procedure" not in model.calls[0][0].content, "level 2 body is not loaded until asked"
    loaded = next(e for e in events if e.type == "skill_loaded")
    assert loaded.data["name"] == "expense-report" and loaded.data["tokens"] > 50
    ref = [e for e in events if e.type == "tool_result"][1]
    assert "Hotel: up to 600" in ref.data["content"]


async def test_unknown_skill_and_path_escape_are_error_results(runner, skills) -> None:
    thread = Thread()
    script = [
        tool_call_response("load_skill", {"name": "nonexistent"}, call_id="s1"),
        tool_call_response("read_skill_reference", {"skill": "expense-report", "path": "../../pyproject.toml"}, call_id="s2"),
        ModelResponse(content="I do not have that skill."),
    ]
    events, _, _ = await drive(thread, script, runner, skills=skills)
    results = [e for e in events if e.type == "tool_result"]
    assert results[0].data["is_error"] and "unknown skill" in results[0].data["content"]
    assert results[1].data["is_error"] and "escapes" in results[1].data["content"]
    assert "skill_loaded" not in types(events)


async def test_context_drops_oldest_turns_and_shapes_big_tool_results(runner, registry) -> None:
    registry.register(Tool(ToolSpec("dump", "Return a lot of text.", {"type": "object", "properties": {}}), lambda a: "row;" * 5_000))
    thread = Thread()
    for i in range(20):
        thread.append("user_message", content=f"question {i} " + "filler " * 60)
        thread.append("assistant_message", content=f"answer {i} " + "filler " * 60, tool_calls=[])
    script = [tool_call_response("dump", {}, call_id="d1"), ModelResponse(content="Lots of rows.")]
    events, _, model = await drive(thread, script, runner, allowlist={"dump"}, context_budget=1_500, user_content="dump it")
    first_call, second_call = model.calls[0], model.calls[1]
    assert len(first_call) < 41, "old turns were dropped to fit the budget"
    assert first_call[1].role == "user", "trimming keeps whole turns, so the history still starts at a user message"
    report = [e for e in events if e.type == "assistant_message"][0].data["context"]
    assert report["dropped_messages"] > 0
    tool_msg = [m for m in second_call if m.role == "tool"][0]
    assert "chars omitted" in tool_msg.content and len(tool_msg.content) < 3_000
    assert len([e for e in events if e.type == "tool_result"][0].data["content"]) == 20_000, "the thread keeps the full result"
