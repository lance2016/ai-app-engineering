"""Retrieval is per user and per relevance; forgetting is targeted and audited.

Long-term memory is not "dump everything into the prompt". The runtime picks a
few memories relevant to the current request for *this* user. When the user
says "forget what I told you about my daughter", the runtime deletes exactly
the memories whose provenance matches and writes an audit event, so the
deletion itself can be proven later.

Run:  uv run python lessons/14-memory/code/03_retrieve_and_forget.py
Expect: retrieval for a restaurant request returns diet memories but not the
        unrelated one; the forget request removes one memory and leaves an audit line.
"""

# %% imports
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


# %% store
@dataclass(frozen=True)
class Memory:
    id: str
    user_id: str
    content: str
    subject: str
    keywords: tuple[str, ...]
    source_thread: str
    source_event_ids: tuple[int, ...]


MEMORIES = [
    Memory("m1", "u42", "cannot eat spicy food", "spice", ("spicy", "food", "restaurant"), "thr_u42_01", (2,)),
    Memory("m2", "u42", "has a vegetarian daughter", "family", ("daughter", "vegetarian", "restaurant"), "thr_u42_01", (2,)),
    Memory("m3", "u42", "prefers morning meetings", "schedule", ("meeting", "morning", "calendar"), "thr_u42_07", (3,)),
    Memory("m4", "u99", "is allergic to peanuts", "allergy", ("peanut", "allergy", "food"), "thr_u99_02", (1,)),
]
AUDIT: list[dict] = []


# %% retrieve
def retrieve(memories: list[Memory], *, user_id: str, query: str, k: int = 3) -> list[Memory]:
    """Tenant filter first, relevance second. The other user's memories must never appear."""
    words = set(query.lower().split())
    scored = [(len(words & set(m.keywords)), m) for m in memories if m.user_id == user_id]
    scored = [(s, m) for s, m in scored if s > 0]
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:k]]


# %% forget
def forget(memories: list[Memory], *, user_id: str, subject: str, requested_by: str) -> list[Memory]:
    """Delete by provenance-bearing subject; record what was removed and why."""
    removed = [m for m in memories if m.user_id == user_id and m.subject == subject]
    kept = [m for m in memories if m not in removed]
    AUDIT.append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "action": "forget",
        "user_id": user_id,
        "subject": subject,
        "requested_by": requested_by,
        "removed": [{"id": m.id, "source_thread": m.source_thread, "source_event_ids": list(m.source_event_ids)} for m in removed],
    })
    return kept


# %% run
def main() -> None:
    query = "recommend a restaurant for dinner"
    hits = retrieve(MEMORIES, user_id="u42", query=query)
    print(f"context for {query!r}: {[m.content for m in hits]}")
    assert all(m.user_id == "u42" for m in hits), "tenant leak"

    remaining = forget(MEMORIES, user_id="u42", subject="family", requested_by="user")
    print(f"after forget(family): {[m.content for m in remaining if m.user_id == 'u42']}")
    print("audit:", json.dumps(AUDIT[-1], ensure_ascii=False))

    hits_after = retrieve(remaining, user_id="u42", query=query)
    print(f"context after forget: {[m.content for m in hits_after]}")
    assert not any(m.subject == "family" for m in hits_after)


if __name__ == "__main__":
    main()
