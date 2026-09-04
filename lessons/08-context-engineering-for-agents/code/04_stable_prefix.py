"""Cache-friendly layout: put what never changes first, what changes every turn last.

Providers cache the longest prefix they have already seen. A timestamp or a
per-request id near the top of the system prompt invalidates the cache on
every call. This script simulates ten turns and hashes the prefix each time:
a stable layout hits the cache from turn two onward; a volatile one never does.

Run:  uv run python lessons/08-context-engineering-for-agents/code/04_stable_prefix.py
      INJECT_VOLATILE_PREFIX=1 uv run python lessons/08-context-engineering-for-agents/code/04_stable_prefix.py
Expect: 9/10 cache hits with the stable layout, 0/10 with the volatile one.
"""

# %% imports
import hashlib
import os
from datetime import UTC, datetime

from aiapp import Message

INJECT_VOLATILE_PREFIX = os.environ.get("INJECT_VOLATILE_PREFIX") == "1"
TOOLS_BLOCK = "Tools: search(q), read(id), summarize(text). Use one at a time. Cite sources."
RULES = "You are a research assistant. " * 20  # long, stable instructions


# %% layouts
def build_window(turn: int, history: list[Message]) -> list[Message]:
    now = datetime.now(UTC).isoformat()
    if INJECT_VOLATILE_PREFIX:
        system = f"Current time: {now}\nRequest #{turn}\n{RULES}\n{TOOLS_BLOCK}"
        return [Message(role="system", content=system), *history]
    system = f"{RULES}\n{TOOLS_BLOCK}"
    # volatile facts travel in the *last* message, after the cacheable prefix
    return [Message(role="system", content=system), *history, Message(role="user", content=f"(current time: {now})")]


def prefix_hash(window: list[Message], n_messages: int) -> str:
    text = "\n".join(m.content for m in window[:n_messages])
    return hashlib.sha256(text.encode()).hexdigest()[:10]


# %% simulate
def main() -> None:
    history: list[Message] = []
    seen: set[str] = set()
    hits = 0
    for turn in range(1, 11):
        history.append(Message(role="user", content=f"turn {turn} question"))
        window = build_window(turn, history)
        h = prefix_hash(window, 1)  # the system message is the cacheable unit here
        hit = h in seen
        hits += hit
        seen.add(h)
        print(f"turn {turn:2}: prefix={h} {'HIT ' if hit else 'MISS'}")
        history.append(Message(role="assistant", content=f"answer {turn}"))
    prefix_tokens = len(RULES + TOOLS_BLOCK) // 4
    print(f"\nlayout={'volatile' if INJECT_VOLATILE_PREFIX else 'stable'}: {hits}/10 prefix cache hits; ~{prefix_tokens} prefix tokens billed at cache rate on each hit")


if __name__ == "__main__":
    main()
