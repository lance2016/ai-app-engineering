"""Tool-selection accuracy: 20 user messages, each with the tool the agent should pick first.

Offline the fake model is scripted with the expected call, so the harness itself
is what is being tested and the accuracy is 100%. With MODEL_PROVIDER set to a
real provider the same cases measure the real model and print a per-case table;
the recorded number is the baseline for M5's evaluation gate.
"""

import asyncio
import os

import pytest

from aiapp import FakeAdapter, Message, ModelResponse, get_adapter, tool_call_response
from aiapp.runtime import ContextBuilder, ToolRegistry
from aiapp.runtime.loop import REQUEST_HUMAN_INPUT_SPEC
from aiapp.thread import Thread
from aiapp.tools.demo import DocStore

CASES: list[tuple[str, str | None]] = [
    ("What is your refund policy?", "search_docs"),
    ("How much is shipping to Germany?", "search_docs"),
    ("Do orders over 50 ship free?", "search_docs"),
    ("Show me the document doc_refunds", "read_doc"),
    ("Open doc_shipping please", "read_doc"),
    ("Read the returns draft", "search_docs"),
    ("Delete doc_returns_draft, it is obsolete", "delete_doc"),
    ("Remove the shipping document", "search_docs"),
    ("Please get rid of doc_refunds", "delete_doc"),
    ("Is there anything about international delivery?", "search_docs"),
    ("Hi!", None),
    ("Thanks, that is all.", None),
    ("What can you help me with?", None),
    ("Review my expenses: hotel 650, dinner 45", "load_skill"),
    ("Are these reimbursable? taxi 30, beer 12", "load_skill"),
    ("Which document should I update, refunds or shipping?", "request_human_input"),
    ("Find the policy on store credit", "search_docs"),
    ("What does doc_refunds say exactly?", "read_doc"),
    ("Tell me a joke", None),
    ("Search for 'receipt'", "search_docs"),
]

MIN_ACCURACY = 0.9


def expected_response(expected: str | None) -> ModelResponse:
    if expected is None:
        return ModelResponse(content="Sure.")
    args = {
        "search_docs": {"query": "policy"}, "read_doc": {"doc_id": "doc_refunds"}, "delete_doc": {"doc_id": "doc_refunds"},
        "load_skill": {"name": "expense-report"}, "request_human_input": {"question": "which?"},
    }[expected]
    return tool_call_response(expected, args)


async def measure() -> tuple[float, list[tuple[str, str | None, str | None]]]:
    registry = ToolRegistry()
    DocStore().register_into(registry)
    from aiapp.runtime import SkillLoader
    from tests.project.m3.conftest import SKILLS_DIR

    skills = SkillLoader(SKILLS_DIR).discover(registry.names())
    skills.register_into(registry)
    specs = [*registry.specs(registry.names()), REQUEST_HUMAN_INPUT_SPEC]
    provider = os.environ.get("MODEL_PROVIDER", "fake").lower()
    model = FakeAdapter(script=[expected_response(e) for _, e in CASES]) if provider == "fake" else get_adapter(provider)
    context = ContextBuilder("You are a document workspace assistant. Use tools when they help; answer directly for small talk.", skill_catalog=skills.catalog())

    rows = []
    for text, expected in CASES:
        thread = Thread()
        thread.append("user_message", content=text)
        reply = await model.complete(context.build(thread), tools=specs)
        picked = reply.tool_calls[0].name if reply.tool_calls else None
        rows.append((text, expected, picked))
    accuracy = sum(1 for _, e, p in rows if e == p) / len(rows)
    return accuracy, rows


def test_tool_selection_accuracy_meets_the_baseline() -> None:
    accuracy, rows = asyncio.run(measure())
    print(f"\n{'user message':52} {'expected':22} {'picked':22} ok")
    for text, expected, picked in rows:
        print(f"{text[:52]:52} {str(expected):22} {str(picked):22} {'yes' if expected == picked else 'NO'}")
    print(f"tool selection accuracy: {accuracy:.0%} over {len(rows)} cases (provider={os.environ.get('MODEL_PROVIDER', 'fake')})")
    assert accuracy >= MIN_ACCURACY


def test_message_type_is_importable() -> None:  # keeps the Message import honest for real-model runs
    assert Message(role="user", content="x").role == "user"


if __name__ == "__main__":  # uv run python tests/project/m3/test_tool_accuracy.py  (with MODEL_PROVIDER=deepseek for a real baseline)
    pytest.main([__file__, "-q", "-s"])
