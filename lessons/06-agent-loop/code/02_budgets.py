"""Stop conditions beyond a step count: tokens and wall-clock time.

Every model call reports usage; the runtime keeps a running total and stops
when any budget is exhausted. Budgets are checked *after* each call, so the
loop always knows why it stopped and can tell the user instead of hanging.

Run:  uv run python lessons/06-agent-loop/code/02_budgets.py
      INJECT_TOKEN_BURN=1 uv run python lessons/06-agent-loop/code/02_budgets.py
      INJECT_SLOW_MODEL=1 uv run python lessons/06-agent-loop/code/02_budgets.py
Expect: finished normally; stopped by token budget; stopped by time budget.
"""

# %% imports
import asyncio
import os
import time
from dataclasses import dataclass
from enum import StrEnum

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response

INJECT_TOKEN_BURN = os.environ.get("INJECT_TOKEN_BURN") == "1"
INJECT_SLOW_MODEL = os.environ.get("INJECT_SLOW_MODEL") == "1"


# %% budget
class StopReason(StrEnum):
    FINISHED = "finished"
    STEP_LIMIT = "step_limit"
    TOKEN_BUDGET = "token_budget"
    TIME_BUDGET = "time_budget"


@dataclass
class Budget:
    max_steps: int
    max_tokens: int
    max_seconds: float
    steps: int = 0
    tokens: int = 0
    started: float = 0.0

    def start(self) -> None:
        self.started = time.monotonic()

    def charge(self, *, tokens: int) -> StopReason | None:
        """Record one iteration and return the first exhausted budget, if any."""
        self.steps += 1
        self.tokens += tokens
        if self.tokens > self.max_tokens:
            return StopReason.TOKEN_BUDGET
        if time.monotonic() - self.started > self.max_seconds:
            return StopReason.TIME_BUDGET
        if self.steps >= self.max_steps:
            return StopReason.STEP_LIMIT
        return None


# %% slow_model
class SlowFake(FakeAdapter):
    async def complete(self, messages, tools=None):
        if INJECT_SLOW_MODEL:
            await asyncio.sleep(0.3)
        return await super().complete(messages, tools)


# %% run_agent
SEARCH = ToolSpec("search", "Search the web.", {"type": "object", "properties": {"q": {"type": "string"}}})


async def run_agent(model: FakeAdapter, goal: str, budget: Budget) -> tuple[StopReason, str]:
    messages = [Message(role="user", content=goal)]
    budget.start()
    while True:
        reply = await model.complete(messages, tools=[SEARCH])
        spent = reply.usage.input_tokens + reply.usage.output_tokens
        if not reply.wants_tool:
            budget.charge(tokens=spent)
            return StopReason.FINISHED, reply.content
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            messages.append(Message(role="tool", tool_call_id=call.id, content=f"results for {call.arguments.get('q')}"))
        exhausted = budget.charge(tokens=spent)
        print(f"step {budget.steps}: tokens so far {budget.tokens}, elapsed {time.monotonic() - budget.started:.2f}s")
        if exhausted:
            return exhausted, ""


# %% script
def build_script() -> list[ModelResponse]:
    filler = "x" * 4000 if INJECT_TOKEN_BURN else ""  # ~1000 tokens of noise per turn
    return [tool_call_response("search", {"q": f"query {i} {filler}"}) for i in range(3)] + [ModelResponse(content="Here is what I found.")]


# %% run
async def main() -> None:
    budget = Budget(max_steps=10, max_tokens=2500, max_seconds=0.5)
    reason, answer = await run_agent(SlowFake(script=build_script()), "Research the topic.", budget)
    print(f"stop_reason={reason} steps={budget.steps} tokens={budget.tokens} answer={answer!r}")


if __name__ == "__main__":
    asyncio.run(main())
