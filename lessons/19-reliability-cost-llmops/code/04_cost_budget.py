"""Cost is a runtime signal, not a monthly surprise.

Every response carries usage. Multiply by the price list, attribute to a
tenant, and compare against a budget while the run is still going. Route
cheap tasks to cheap models. Prices change often, so they live in one table
with a date on it, never scattered through the code.

Run:  uv run python lessons/19-reliability-cost-llmops/code/04_cost_budget.py
      INJECT_RUNAWAY=1 uv run python lessons/19-reliability-cost-llmops/code/04_cost_budget.py
Expect: a normal run prints per-model spend under budget. The runaway loop
        keeps calling the expensive model until the budget stops it.
"""

# %% imports
import os
from dataclasses import dataclass, field

from aiapp import ModelResponse, Usage

INJECT_RUNAWAY = os.environ.get("INJECT_RUNAWAY") == "1"

# %% price_table
# USD per 1M tokens. ILLUSTRATIVE NUMBERS as of 2026-09-04; every provider changes these.
# Load from config in a real service and record the date next to the values.
PRICES_USD_PER_M = {
    "small-fast": {"in": 0.15, "out": 0.60},
    "large-smart": {"in": 2.50, "out": 10.00},
}
PRICES_AS_OF = "2026-09-04"


# %% cost_meter
@dataclass
class CostMeter:
    budget_usd: float
    warn_at: float = 0.8
    spent_usd: float = 0.0
    by_model: dict[str, float] = field(default_factory=dict)
    warned: bool = False

    def charge(self, model: str, usage: Usage) -> float:
        price = PRICES_USD_PER_M[model]
        cost = (usage.input_tokens * price["in"] + usage.output_tokens * price["out"]) / 1_000_000
        self.spent_usd += cost
        self.by_model[model] = self.by_model.get(model, 0.0) + cost
        if not self.warned and self.spent_usd >= self.warn_at * self.budget_usd:
            self.warned = True
            print(f"  ALERT: {self.spent_usd / self.budget_usd:.0%} of budget used")
        return cost

    @property
    def exhausted(self) -> bool:
        return self.spent_usd >= self.budget_usd


# %% routing
def pick_model(task: str) -> str:
    """Classification and short lookups go to the small model; open-ended work to the large one."""
    return "small-fast" if task in {"classify_intent", "extract_fields"} else "large-smart"


def fake_call(model: str, task: str) -> ModelResponse:
    usage = Usage(input_tokens=3_000, output_tokens=600 if model == "large-smart" else 40)
    return ModelResponse(content=f"{model} did {task}", usage=usage)


# %% run
def main() -> None:
    meter = CostMeter(budget_usd=0.05)  # per-conversation budget
    tasks = ["classify_intent", "extract_fields", "draft_reply", "draft_reply"]
    if INJECT_RUNAWAY:
        tasks = ["draft_reply"] * 50  # a loop that never converges
    for step, task in enumerate(tasks, 1):
        if meter.exhausted:
            print(f"stop at step {step}: budget ${meter.budget_usd:.2f} exhausted")
            break
        model = pick_model(task)
        cost = meter.charge(model, fake_call(model, task).usage)
        print(f"step {step:2}: {task:15} -> {model:12} ${cost:.5f}")
    print(f"spent ${meter.spent_usd:.4f} of ${meter.budget_usd:.2f}; by model: "
          + ", ".join(f"{m}=${c:.4f}" for m, c in meter.by_model.items()) + f" (prices as of {PRICES_AS_OF})")


if __name__ == "__main__":
    main()
