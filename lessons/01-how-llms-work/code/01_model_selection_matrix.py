"""Pick a model by hard constraints first, cost second, and never by leaderboard alone.

A candidate that fails one hard constraint (context window, tool calling,
structured output, data residency, latency class) is out, however cheap or
clever. Survivors are ranked by the cost of a *typical conversation*, which
re-sends the growing history every turn.

Every number below is an illustrative assumption dated 2026-09-04. Replace
them with the vendor's price page and your own traffic before deciding.

Run:  uv run python lessons/01-how-llms-work/code/01_model_selection_matrix.py
      INJECT_IGNORE_CONTEXT=1 uv run python lessons/01-how-llms-work/code/01_model_selection_matrix.py
Expect: an elimination table, then survivors ranked by cost per conversation.
        With the injection the context constraint is skipped, a small-window
        model wins on price, and the last turn of the conversation overflows it.
"""

# %% imports
import os
from dataclasses import dataclass

INJECT_IGNORE_CONTEXT = os.environ.get("INJECT_IGNORE_CONTEXT") == "1"
QUOTED_ON = "2026-09-04 (illustrative)"


# %% types
@dataclass(frozen=True)
class Candidate:
    name: str
    context_window: int
    price_in_per_m: float  # USD per 1M input tokens
    price_out_per_m: float
    tool_calling: bool
    structured_output: bool
    residency: str  # where the data goes: "cn", "us", "self"
    latency_class: str  # "fast" | "medium" | "slow"


@dataclass(frozen=True)
class Requirement:
    min_context: int
    needs_tool_calling: bool
    needs_structured_output: bool
    allowed_residency: frozenset[str]
    max_latency_class: str
    turns: int
    fixed_input_per_turn: int  # system prompt + tools + retrieval
    user_tokens_per_turn: int
    output_tokens_per_turn: int


LATENCY_ORDER = {"fast": 0, "medium": 1, "slow": 2}

CANDIDATES = [
    Candidate("hosted-large", 128_000, 2.50, 10.00, True, True, "us", "medium"),
    Candidate("hosted-small", 32_000, 0.15, 0.60, True, True, "us", "fast"),
    Candidate("hosted-cn-large", 128_000, 0.55, 2.20, True, True, "cn", "medium"),
    Candidate("hosted-cn-mini", 4_096, 0.07, 0.28, True, True, "cn", "fast"),
    Candidate("reasoning-large", 200_000, 15.00, 60.00, True, True, "us", "slow"),
    Candidate("open-8b-selfhost", 32_000, 0.20, 0.20, True, True, "self", "fast"),
]


# %% hard constraints
def peak_input_tokens(r: Requirement) -> int:
    """Input of the last turn: fixed part plus every previous exchange re-sent."""
    return r.fixed_input_per_turn + (r.turns - 1) * (r.user_tokens_per_turn + r.output_tokens_per_turn) + r.user_tokens_per_turn


def hard_filter(c: Candidate, r: Requirement) -> list[str]:
    reasons: list[str] = []
    needed = peak_input_tokens(r) + r.output_tokens_per_turn
    if not INJECT_IGNORE_CONTEXT and c.context_window < max(r.min_context, needed):
        reasons.append(f"context {c.context_window} < {max(r.min_context, needed)}")
    if r.needs_tool_calling and not c.tool_calling:
        reasons.append("no tool calling")
    if r.needs_structured_output and not c.structured_output:
        reasons.append("no structured output")
    if c.residency not in r.allowed_residency:
        reasons.append(f"residency {c.residency} not allowed")
    if LATENCY_ORDER[c.latency_class] > LATENCY_ORDER[r.max_latency_class]:
        reasons.append(f"too slow ({c.latency_class})")
    return reasons


# %% cost model
def cost_per_conversation(c: Candidate, r: Requirement) -> float:
    total_in = 0
    history = 0
    for _ in range(r.turns):
        total_in += r.fixed_input_per_turn + history + r.user_tokens_per_turn
        history += r.user_tokens_per_turn + r.output_tokens_per_turn
    total_out = r.turns * r.output_tokens_per_turn
    return total_in / 1e6 * c.price_in_per_m + total_out / 1e6 * c.price_out_per_m


# %% run
def main() -> None:
    req = Requirement(
        min_context=16_000,
        needs_tool_calling=True,
        needs_structured_output=True,
        allowed_residency=frozenset({"cn", "self"}),
        max_latency_class="medium",
        turns=12,
        fixed_input_per_turn=2_400,
        user_tokens_per_turn=60,
        output_tokens_per_turn=250,
    )
    print(f"prices quoted {QUOTED_ON}; peak input at turn {req.turns}: {peak_input_tokens(req)} tokens\n")
    print(f"{'candidate':18} {'verdict':8} reasons")
    survivors: list[Candidate] = []
    for c in CANDIDATES:
        reasons = hard_filter(c, req)
        print(f"{c.name:18} {'out' if reasons else 'in':8} {'; '.join(reasons)}")
        if not reasons:
            survivors.append(c)

    print(f"\n{'survivor':18} {'$/conversation':>15} {'$/1k conv/day':>14}")
    for c in sorted(survivors, key=lambda c: cost_per_conversation(c, req)):
        cost = cost_per_conversation(c, req)
        print(f"{c.name:18} {cost:15.4f} {cost * 1000:14.2f}")

    if survivors:
        winner = min(survivors, key=lambda c: cost_per_conversation(c, req))
        needed = peak_input_tokens(req) + req.output_tokens_per_turn
        if winner.context_window < needed:
            print(f"\n!! {winner.name} won on price but its window ({winner.context_window}) is smaller than the last turn ({needed}).")
            print("   In production this is a 400 from the provider on turn ~8. Constraints before cost, always.")
    print("\ncheapest is not the answer; cheapest *among the survivors* is the start of the conversation.")


if __name__ == "__main__":
    main()
