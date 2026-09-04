"""The context window is a hard budget and every turn spends from it.

System prompt, tool schemas, retrieved documents, the whole conversation so
far and the room you leave for the answer all share one window. History grows
every turn, so the cost of a conversation grows roughly with the square of
its length unless you trim.

Run:  uv run python lessons/01-how-llms-work/code/03_context_window_budget.py
      INJECT_LONG_HISTORY=1 uv run python lessons/01-how-llms-work/code/03_context_window_budget.py
Expect: a per-turn table of tokens by component and cumulative cost. With
        injection the window overflows and the script shows what must be cut.
"""

# %% imports
import os
from dataclasses import dataclass

INJECT_LONG_HISTORY = os.environ.get("INJECT_LONG_HISTORY") == "1"

CONTEXT_WINDOW = 8_000  # small on purpose so the overflow happens in a few turns
PRICE_PER_1K_INPUT = 0.002  # example number; check the provider's pricing page
PRICE_PER_1K_OUTPUT = 0.008


def estimate_tokens(text: str) -> int:
    """Rough: ~4 bytes per token for English, ~1.5 for Chinese. Real tokenizers differ."""
    return max(1, len(text.encode("utf-8")) // 4)


# %% budget
@dataclass
class TurnBudget:
    system: int
    tools: int
    retrieved: int
    history: int
    reserved_for_output: int

    @property
    def used(self) -> int:
        return self.system + self.tools + self.retrieved + self.history + self.reserved_for_output

    def overflow(self, window: int) -> int:
        return max(0, self.used - window)


# %% simulate
def simulate(turns: int, reply_tokens: int) -> None:
    system = estimate_tokens("You are a helpful assistant for an online bookstore. " * 12)
    tools = 3 * 120  # three tool schemas
    retrieved = 800  # two retrieved passages
    reserved = 600
    history = 0
    total_input = 0
    print(f"window={CONTEXT_WINDOW}  fixed per turn: system={system} tools={tools} retrieved={retrieved} reserved={reserved}\n")
    print(f"{'turn':>4} {'history':>8} {'used':>6} {'overflow':>8} {'cum. input tokens':>18} {'cum. cost $':>11}")
    for turn in range(1, turns + 1):
        b = TurnBudget(system, tools, retrieved, history, reserved)
        total_input += b.used - reserved
        cost = total_input / 1000 * PRICE_PER_1K_INPUT + turn * reply_tokens / 1000 * PRICE_PER_1K_OUTPUT
        flag = "  <- must trim" if b.overflow(CONTEXT_WINDOW) else ""
        print(f"{turn:4} {history:8} {b.used:6} {b.overflow(CONTEXT_WINDOW):8} {total_input:18} {cost:11.4f}{flag}")
        history += 60 + reply_tokens  # user question + assistant reply join the history
    print("\ninput tokens re-sent every turn dominate the bill; the reply is the small part.")
    if INJECT_LONG_HISTORY:
        print("overflow options, cheapest first: drop old turns, summarise them, retrieve less, shrink tool schemas.")


# %% run
def main() -> None:
    simulate(turns=12 if INJECT_LONG_HISTORY else 6, reply_tokens=700 if INJECT_LONG_HISTORY else 250)


if __name__ == "__main__":
    main()
