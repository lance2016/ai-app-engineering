"""New memories are merged into the store, not appended blindly.

Consolidation does three things: drop exact duplicates, resolve conflicts
(newer statement about the same subject wins, old one is kept as history),
and expire episodes that are too old to matter. Skip it and the model gets
handed "user is vegetarian" and "user eats steak" in the same prompt.

Run:  uv run python lessons/14-memory/code/02_consolidate.py
      INJECT_NO_CONSOLIDATION=1 uv run python lessons/14-memory/code/02_consolidate.py
Expect: 5 candidates collapse into 3 active memories; with injection all 5 are
        kept and the retrieval for "diet" returns a contradiction.
"""

# %% imports
import os
from dataclasses import dataclass, field, replace
from datetime import date, timedelta

INJECT_NO_CONSOLIDATION = os.environ.get("INJECT_NO_CONSOLIDATION") == "1"
EPISODE_TTL_DAYS = 180


# %% types
@dataclass(frozen=True)
class Memory:
    content: str
    kind: str  # preference | fact | episode
    subject: str  # what the memory is about; conflicts are resolved per subject
    observed_on: date
    source_event_ids: tuple[int, ...]
    superseded_by: str | None = None  # content of the newer memory, if any


@dataclass
class MemoryStore:
    active: list[Memory] = field(default_factory=list)
    history: list[Memory] = field(default_factory=list)

    def add(self, candidate: Memory, *, today: date) -> str:
        if candidate.kind == "episode" and today - candidate.observed_on > timedelta(days=EPISODE_TTL_DAYS):
            return "expired"
        for existing in self.active:
            if existing.content == candidate.content:
                return "duplicate"
            if existing.subject == candidate.subject and existing.kind != "episode":
                # conflict on the same subject: newer wins, older becomes history
                self.active.remove(existing)
                self.history.append(replace(existing, superseded_by=candidate.content))
                self.active.append(candidate)
                return f"superseded {existing.content!r}"
        self.active.append(candidate)
        return "added"

    def add_unchecked(self, candidate: Memory) -> str:
        self.active.append(candidate)
        return "appended"

    def about(self, subject: str) -> list[Memory]:
        return [m for m in self.active if m.subject == subject]


# %% candidates
TODAY = date(2026, 9, 4)
CANDIDATES = [
    Memory("is vegetarian", "preference", "diet", date(2025, 3, 1), (2,)),
    Memory("cannot eat spicy food", "preference", "spice", date(2025, 3, 1), (2,)),
    Memory("cannot eat spicy food", "preference", "spice", date(2026, 1, 9), (7,)),  # exact duplicate
    Memory("started eating fish again, no longer vegetarian", "preference", "diet", date(2026, 8, 20), (11,)),  # conflict
    Memory("had a bad experience at Sea Breeze", "episode", "sea_breeze", date(2025, 11, 2), (4,)),  # > 180 days old
]


# %% run
def main() -> None:
    store = MemoryStore()
    for c in CANDIDATES:
        outcome = store.add_unchecked(c) if INJECT_NO_CONSOLIDATION else store.add(c, today=TODAY)
        print(f"{outcome:40} <- {c.content!r}")
    print(f"\nactive={len(store.active)} history={len(store.history)}")
    diet = store.about("diet")
    print(f"what the model would be told about diet: {[m.content for m in diet]}")
    if len(diet) > 1:
        print("CONTRADICTION: two active memories on the same subject; the model will pick one at random")
    else:
        print(f"history keeps the old statement: {[h.content for h in store.history]}")


if __name__ == "__main__":
    main()
