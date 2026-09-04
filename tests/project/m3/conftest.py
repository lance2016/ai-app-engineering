"""M3 fixtures: a registry over the demo DocStore, an in-memory runner, and a helper that drives run_agent."""

from collections.abc import Iterable

import pytest

from aiapp import FakeAdapter, ModelResponse, Thread
from aiapp.runtime import Budget, ContextBuilder, RunContext, SkillLoader, ToolRegistry, ToolRunner, run_agent
from aiapp.runtime.turn import Delta
from aiapp.storage.memory import InMemoryKeyValueStore
from aiapp.thread import Event
from aiapp.tools.demo import DocStore

from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[3] / "project/skills"
ALL_TOOLS = frozenset({"search_docs", "read_doc", "delete_doc", "load_skill", "read_skill_reference"})


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def docs() -> DocStore:
    return DocStore()


@pytest.fixture
def registry(docs: DocStore) -> ToolRegistry:
    reg = ToolRegistry()
    docs.register_into(reg)
    return reg


@pytest.fixture
def skills(registry: ToolRegistry) -> SkillLoader:
    loader = SkillLoader(SKILLS_DIR).discover(registry.names())
    loader.register_into(registry)
    return loader


@pytest.fixture
def kv() -> InMemoryKeyValueStore:
    return InMemoryKeyValueStore()


@pytest.fixture
def runner(registry: ToolRegistry, kv: InMemoryKeyValueStore) -> ToolRunner:
    return ToolRunner(registry, kv, retry_base_delay_s=0.001)


def ctx_for(thread: Thread, allowlist: Iterable[str] = ALL_TOOLS) -> RunContext:
    return RunContext(tenant_id="tenant-a", thread_id=thread.thread_id, allowlist=frozenset(allowlist))


async def drive(
    thread: Thread,
    script: list[ModelResponse],
    runner: ToolRunner,
    *,
    skills: SkillLoader | None = None,
    user_content: str | None = "hi",
    budget: Budget | None = None,
    allowlist: Iterable[str] = ALL_TOOLS,
    timeout_s: float = 1.0,
    context_budget: int = 24_000,
    model: FakeAdapter | None = None,
) -> tuple[list[Event], str, FakeAdapter]:
    """Run the loop to its next stop; return (events yielded, streamed text, model)."""
    model = model or FakeAdapter(script=script, chunk_size=8)
    context = ContextBuilder("You are a workspace assistant.", budget_tokens=context_budget, skill_catalog=skills.catalog() if skills else "")
    events: list[Event] = []
    text: list[str] = []
    async for item in run_agent(
        thread, model, runner, ctx=ctx_for(thread, allowlist), budget=budget or Budget(max_steps=6),
        context=context, skills=skills, timeout_s=timeout_s, user_content=user_content,
    ):
        if isinstance(item, Delta):
            text.append(item.content)
        else:
            events.append(item)
    return events, "".join(text), model


def types(events: list[Event]) -> list[str]:
    return [e.type for e in events]
