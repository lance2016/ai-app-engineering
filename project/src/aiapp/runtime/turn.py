"""``Delta`` (a streamed text increment) and ``run_turn``: the M1 loop, now a thin wrapper over the agent loop.

M1 shipped a tool-less turn. M3 replaced it with ``run_agent``; ``run_turn`` keeps
the M1 shape (no tools, no skills) so lesson 02's description of the streaming
path still points at real code.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass

from aiapp.adapters.base import ModelAdapter
from aiapp.thread import Event, Thread


@dataclass(frozen=True)
class Delta:
    """A streamed text increment. Shown to the client, never stored: the thread keeps the whole message."""

    content: str


async def run_turn(
    thread: Thread,
    model: ModelAdapter,
    *,
    system_prompt: str,
    user_content: str,
    timeout_s: float,
) -> AsyncIterator[Event | Delta]:
    from aiapp.runtime.budget import Budget
    from aiapp.runtime.context import ContextBuilder
    from aiapp.runtime.loop import run_agent
    from aiapp.runtime.registry import ToolRegistry
    from aiapp.runtime.runner import RunContext, ToolRunner
    from aiapp.storage.memory import InMemoryKeyValueStore

    runner = ToolRunner(ToolRegistry(), InMemoryKeyValueStore())
    ctx = RunContext(tenant_id="local", thread_id=thread.thread_id, allowlist=frozenset())
    async for item in run_agent(
        thread, model, runner, ctx=ctx, budget=Budget(max_steps=1), context=ContextBuilder(system_prompt),
        timeout_s=timeout_s, user_content=user_content,
    ):
        yield item
