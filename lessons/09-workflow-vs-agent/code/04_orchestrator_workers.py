"""Orchestrator-workers: the plan is decided at runtime, the execution is still bounded.

An orchestrator model breaks the task into sub-tasks as structured output. The
runtime validates the plan (count, allowed kinds), runs a worker per sub-task
in parallel, then hands the results back for synthesis. Unlike a fixed chain,
the number of steps is unknown up front; unlike a free agent, it is capped.

Run:  uv run python lessons/09-workflow-vs-agent/code/04_orchestrator_workers.py
      INJECT_HUGE_PLAN=1 uv run python lessons/09-workflow-vs-agent/code/04_orchestrator_workers.py
Expect: a 3-item plan, three workers, one synthesis. With injection the
        orchestrator proposes 40 sub-tasks and the runtime refuses the plan.
"""

# %% imports
import asyncio
import json
import os

from pydantic import BaseModel, Field, ValidationError

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_HUGE_PLAN = os.environ.get("INJECT_HUGE_PLAN") == "1"


# %% plan_schema
class SubTask(BaseModel):
    kind: str = Field(pattern="^(read|search|compute)$")
    description: str


class Plan(BaseModel):
    subtasks: list[SubTask] = Field(max_length=8)  # the cap is part of the contract


# %% roles
async def orchestrate(model: FakeAdapter, task: str) -> Plan:
    reply = await model.complete([Message(role="system", content="Return JSON {subtasks:[{kind, description}]}."), Message(role="user", content=task)])
    return Plan.model_validate_json(reply.content)


async def worker(sub: SubTask) -> str:
    model = FakeAdapter(script=[ModelResponse(content=f"done: {sub.description}")])
    reply = await model.complete([Message(role="user", content=sub.description)])
    return reply.content


async def synthesize(model: FakeAdapter, results: list[str]) -> str:
    reply = await model.complete([Message(role="user", content="Combine:\n" + "\n".join(results))])
    return reply.content


# %% run
async def main() -> None:
    n = 40 if INJECT_HUGE_PLAN else 3
    plan_json = json.dumps({"subtasks": [{"kind": ["read", "search", "compute"][i % 3], "description": f"subtask {i}"} for i in range(n)]})
    orchestrator = FakeAdapter(script=[ModelResponse(content=plan_json), ModelResponse(content="Report: all three parts combined.")])
    try:
        plan = await orchestrate(orchestrator, "Analyse Q3 churn.")
    except ValidationError as exc:
        print(f"plan rejected: {exc.errors()[0]['msg']}")
        return
    print(f"plan accepted: {len(plan.subtasks)} subtasks")
    results = await asyncio.gather(*(worker(s) for s in plan.subtasks))
    print("\n".join(f"  {r}" for r in results))
    print("synthesis:", await synthesize(orchestrator, list(results)))


if __name__ == "__main__":
    asyncio.run(main())
