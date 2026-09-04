"""A weighted decision matrix, and why its real output is the sensitivity check.

Scores and weights are opinions. The matrix is useful not because it picks a
winner but because it shows which single assumption would flip the result.
That assumption is what you go and verify before committing.

Run:  uv run python lessons/23-system-design-decisions/code/03_decision_matrix.py
Expect: a ranking for "Build vs Buy vs Open-source" and the list of weight
        changes that would overturn it.
"""

# %% imports
from dataclasses import dataclass


# %% model
@dataclass(frozen=True)
class Criterion:
    name: str
    weight: float  # 0..1, weights sum to 1


OPTIONS = ["Build in-house", "Buy SaaS eval platform", "Self-host open-source"]
CRITERIA = [
    Criterion("time to first value", 0.25),
    Criterion("fit to our agent trace format", 0.25),
    Criterion("data residency / compliance", 0.20),
    Criterion("3-year cost", 0.15),
    Criterion("exit cost if we leave", 0.15),
]
# rows = options, columns = criteria, scores 1..5
SCORES = {
    "Build in-house": [1, 5, 5, 2, 5],
    "Buy SaaS eval platform": [5, 3, 2, 3, 2],
    "Self-host open-source": [3, 4, 5, 4, 4],
}


# %% compute
def total(option: str, weights: list[float]) -> float:
    return sum(s * w for s, w in zip(SCORES[option], weights))


def rank(weights: list[float]) -> list[tuple[str, float]]:
    return sorted(((o, total(o, weights)) for o in OPTIONS), key=lambda t: -t[1])


def flips(step: float = 0.10) -> list[str]:
    """Move `step` of weight from one criterion to another; report when the winner changes."""
    base = [c.weight for c in CRITERIA]
    winner = rank(base)[0][0]
    found = []
    for i, src in enumerate(CRITERIA):
        for j, dst in enumerate(CRITERIA):
            if i == j or base[i] < step:
                continue
            w = base.copy()
            w[i] -= step
            w[j] += step
            new = rank(w)[0][0]
            if new != winner:
                found.append(f"move {step:.0%} weight from '{src.name}' to '{dst.name}' -> {new}")
    return found


# %% run
def main() -> None:
    weights = [c.weight for c in CRITERIA]
    for option, score in rank(weights):
        print(f"{option:26}{score:5.2f}")
    print("\nwhat would flip the decision:")
    for line in flips() or ["nothing within a 10% weight shift; the decision is robust"]:
        print("  " + line)


if __name__ == "__main__":
    main()
