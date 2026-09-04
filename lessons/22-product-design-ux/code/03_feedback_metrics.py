"""Turn thumbs and edits into numbers you can act on.

Feedback is attached to the thread event it refers to, carries a reason code,
and is aggregated by slice. Acceptance rate alone hides problems; the same
table split by intent shows where the product actually fails.

Run:  uv run python lessons/22-product-design-ux/code/03_feedback_metrics.py
Expect: an overall row that looks fine and a per-intent table where one slice
        clearly does not.
"""

# %% imports
from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum


# %% feedback_model
class Signal(StrEnum):
    ACCEPT = "accept"  # used as-is
    EDIT = "edit"  # used after changing it
    REJECT = "reject"  # thumbs down / regenerate
    ESCALATE = "escalate"  # handed to a human


class Reason(StrEnum):
    WRONG_FACT = "wrong_fact"
    TOO_LONG = "too_long"
    MISSED_INTENT = "missed_intent"
    UNSAFE_ACTION = "unsafe_action"
    NONE = ""


@dataclass(frozen=True)
class Feedback:
    thread_id: str
    event_index: int  # which assistant_message this is about
    intent: str  # slice key, set by the runtime's router
    signal: Signal
    reason: Reason = Reason.NONE


# %% aggregate
def summarize(rows: list[Feedback]) -> dict[str, dict[str, float]]:
    by_slice: dict[str, list[Feedback]] = defaultdict(list)
    for r in rows:
        by_slice["ALL"].append(r)
        by_slice[r.intent].append(r)
    out: dict[str, dict[str, float]] = {}
    for key, items in by_slice.items():
        n = len(items)
        out[key] = {
            "n": n,
            "accept": sum(i.signal == Signal.ACCEPT for i in items) / n,
            "edit": sum(i.signal == Signal.EDIT for i in items) / n,
            "reject": sum(i.signal == Signal.REJECT for i in items) / n,
            "escalate": sum(i.signal == Signal.ESCALATE for i in items) / n,
        }
    return out


def top_reason(rows: list[Feedback], intent: str) -> str:
    counts: dict[Reason, int] = defaultdict(int)
    for r in rows:
        if r.intent == intent and r.reason:
            counts[r.reason] += 1
    return max(counts, key=counts.get) if counts else "-"


# %% run
def main() -> None:
    rows = [
        *[Feedback(f"t{i}", 1, "faq", Signal.ACCEPT) for i in range(40)],
        *[Feedback(f"t{i}", 1, "faq", Signal.EDIT, Reason.TOO_LONG) for i in range(5)],
        *[Feedback(f"t{i}", 1, "order_status", Signal.ACCEPT) for i in range(20)],
        *[Feedback(f"t{i}", 1, "order_status", Signal.REJECT, Reason.WRONG_FACT) for i in range(3)],
        *[Feedback(f"t{i}", 2, "refund", Signal.ACCEPT) for i in range(6)],
        *[Feedback(f"t{i}", 2, "refund", Signal.ESCALATE, Reason.UNSAFE_ACTION) for i in range(9)],
        *[Feedback(f"t{i}", 2, "refund", Signal.REJECT, Reason.MISSED_INTENT) for i in range(5)],
    ]
    table = summarize(rows)
    print(f"{'slice':14}{'n':>5}{'accept':>9}{'edit':>7}{'reject':>8}{'escalate':>10}  top reason")
    for key in ["ALL"] + sorted(k for k in table if k != "ALL"):
        m = table[key]
        print(f"{key:14}{m['n']:>5}{m['accept']:>9.0%}{m['edit']:>7.0%}{m['reject']:>8.0%}{m['escalate']:>10.0%}  {top_reason(rows, key) if key != 'ALL' else ''}")


if __name__ == "__main__":
    main()
