"""Where randomness comes from: sampling the next token from a distribution.

The model outputs one score per vocabulary entry. Temperature reshapes those
scores before they become probabilities; top-p cuts off the unlikely tail.
Sample the same distribution a thousand times and the effect is obvious.

Run:  uv run python prerequisites/llm-foundations/04-context-window-and-sampling/code/01_sampling_temperature.py
      TEMPERATURE=0.2 uv run python prerequisites/llm-foundations/04-context-window-and-sampling/code/01_sampling_temperature.py
      TEMPERATURE=2.0 uv run python prerequisites/llm-foundations/04-context-window-and-sampling/code/01_sampling_temperature.py
Expect: at low temperature almost every sample is the top token; at high
        temperature the tail tokens show up. Greedy (temperature 0) never varies.
"""

# %% imports
import math
import os
import random
from collections import Counter

TEMPERATURE = float(os.environ.get("TEMPERATURE", "1.0"))
TOP_P = float(os.environ.get("TOP_P", "1.0"))

# Scores the model might emit after "The capital of France is". Made up, but shaped like real logits.
LOGITS = {"Paris": 6.0, "the": 3.5, "a": 3.0, "located": 2.5, "Lyon": 1.0, "Berlin": 0.5, "banana": -2.0}


# %% softmax_with_temperature
def softmax(logits: dict[str, float], temperature: float) -> dict[str, float]:
    if temperature == 0:  # greedy: all mass on the argmax
        best = max(logits, key=logits.get)
        return {tok: float(tok == best) for tok in logits}
    scaled = {tok: score / temperature for tok, score in logits.items()}
    m = max(scaled.values())
    exps = {tok: math.exp(v - m) for tok, v in scaled.items()}
    total = sum(exps.values())
    return {tok: v / total for tok, v in exps.items()}


# %% top_p
def top_p(probs: dict[str, float], p: float) -> dict[str, float]:
    """Keep the smallest set of tokens whose cumulative probability reaches p, then renormalise."""
    kept: dict[str, float] = {}
    cumulative = 0.0
    for tok, pr in sorted(probs.items(), key=lambda kv: -kv[1]):
        kept[tok] = pr
        cumulative += pr
        if cumulative >= p:
            break
    total = sum(kept.values())
    return {tok: pr / total for tok, pr in kept.items()}


def sample(probs: dict[str, float], rng: random.Random) -> str:
    return rng.choices(list(probs), weights=list(probs.values()))[0]


# %% run
def main() -> None:
    probs = top_p(softmax(LOGITS, TEMPERATURE), TOP_P)
    rng = random.Random(0)
    counts = Counter(sample(probs, rng) for _ in range(1000))
    print(f"temperature={TEMPERATURE} top_p={TOP_P}\n")
    print(f"{'token':10} {'prob':>7} {'sampled/1000':>13}")
    for tok in LOGITS:
        print(f"{tok:10} {probs.get(tok, 0.0):7.3f} {counts.get(tok, 0):13}")
    distinct = len(counts)
    print(f"\n{distinct} distinct tokens appeared. temperature does not make the model smarter or dumber;")
    print("it decides how often the second-best answer wins. 'banana' is always possible unless you cut the tail.")


if __name__ == "__main__":
    main()
