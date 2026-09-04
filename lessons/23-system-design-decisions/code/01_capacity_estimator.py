"""Back-of-envelope capacity and cost for an AI service, with scenarios.

Every system design answer needs numbers: requests per second at peak, tokens
per day, model spend, concurrent runs, database writes. This script derives
them from a handful of assumptions and shows how two levers (prompt caching
and routing simple turns to a cheaper model) change the bill.

Run:  uv run python lessons/23-system-design-decisions/code/01_capacity_estimator.py
Expect: a table of derived numbers for a baseline and two scenarios.
"""

# %% imports
from dataclasses import dataclass, replace
import os


# %% assumptions
@dataclass(frozen=True)
class Assumptions:
    daily_active_users: int
    turns_per_user_per_day: float
    input_tokens_per_turn: int  # system prompt + history + retrieved chunks
    output_tokens_per_turn: int
    tool_calls_per_turn: float
    peak_factor: float  # peak RPS / average RPS
    p95_turn_seconds: float
    price_in_per_mtok: float  # USD per million input tokens
    price_out_per_mtok: float
    cache_hit_ratio: float = 0.0  # share of input tokens served from prompt cache
    cached_price_ratio: float = 0.1  # cached input costs this fraction of full price
    cheap_route_share: float = 0.0  # share of turns routed to a cheaper model
    cheap_price_ratio: float = 0.2  # cheaper model costs this fraction


# %% derive
@dataclass(frozen=True)
class Estimate:
    turns_per_day: float
    avg_rps: float
    peak_rps: float
    peak_concurrent_runs: float
    tokens_in_per_day: float
    tokens_out_per_day: float
    daily_cost_usd: float
    event_writes_per_second_peak: float


def estimate(a: Assumptions) -> Estimate:
    turns = a.daily_active_users * a.turns_per_user_per_day
    avg_rps = turns / 86_400
    peak_rps = avg_rps * a.peak_factor
    concurrent = peak_rps * a.p95_turn_seconds  # Little's law
    tok_in = turns * a.input_tokens_per_turn
    tok_out = turns * a.output_tokens_per_turn
    effective_in_price = a.price_in_per_mtok * ((1 - a.cache_hit_ratio) + a.cache_hit_ratio * a.cached_price_ratio)
    blended = (1 - a.cheap_route_share) + a.cheap_route_share * a.cheap_price_ratio
    cost = (tok_in / 1e6 * effective_in_price + tok_out / 1e6 * a.price_out_per_mtok) * blended
    # one turn writes: user_message, assistant_message(s), tool_result(s), run_finished
    writes_per_turn = 3 + 2 * a.tool_calls_per_turn
    return Estimate(turns, avg_rps, peak_rps, concurrent, tok_in, tok_out, cost, peak_rps * writes_per_turn)


# %% run
def show(label: str, e: Estimate) -> None:
    print(f"{label:28}{e.turns_per_day:>12,.0f}{e.peak_rps:>10.1f}{e.peak_concurrent_runs:>12.0f}{e.tokens_in_per_day/1e6:>10.1f}M{e.daily_cost_usd:>11,.0f}{e.event_writes_per_second_peak:>10.0f}")


def main() -> None:
    base = Assumptions(
        daily_active_users=50_000, turns_per_user_per_day=6, input_tokens_per_turn=6_000,
        output_tokens_per_turn=300, tool_calls_per_turn=1.2, p95_turn_seconds=8,
        price_in_per_mtok=0.5, price_out_per_mtok=1.5,
        peak_factor=20 if os.environ.get("INJECT_TRAFFIC_SPIKE") else 4,
    )
    with_cache = replace(base, cache_hit_ratio=0.6)
    with_routing = replace(with_cache, cheap_route_share=0.5)
    print(f"{'scenario':28}{'turns/day':>12}{'peak rps':>10}{'concurrent':>12}{'in tok/day':>11}{'USD/day':>11}{'writes/s':>10}")
    show("baseline", estimate(base))
    show("+ prompt cache 60%", estimate(with_cache))
    show("+ route 50% to cheap model", estimate(with_routing))
    print("\nconcurrent runs = peak rps x p95 seconds (Little's law); size the worker pool and DB connections from it.")


if __name__ == "__main__":
    main()
