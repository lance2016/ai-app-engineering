"""One attention head by hand: dot products, softmax, weighted sum. Nothing else.

Four tokens, three dimensions, Q/K/V given directly (a real model computes
them with learned matrices). Watch the weights: a token whose Query matches
several Keys spreads its attention; the causal mask blanks out the future.

Run:  uv run python prerequisites/llm-foundations/03-attention-and-transformer/code/01_single_head_attention.py
      CAUSAL=0 uv run python prerequisites/llm-foundations/03-attention-and-transformer/code/01_single_head_attention.py
Expect: per-token attention weights and outputs; with CAUSAL=0 token 0 can see everything.
"""

# %% imports
import math
import os

CAUSAL = os.environ.get("CAUSAL", "1") == "1"


# %% helpers
def softmax(xs: list[float]) -> list[float]:
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]
    s = sum(exps)
    return [e / s for e in exps]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


# %% data: four tokens already projected to Q, K, V
Q = [[1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1]]
K = [[1, 0, 0], [0, 1, 0], [1, 1, 0], [0, 0, 1]]
V = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 1]]
D = 3


# %% one head
def attend(i: int, causal: bool) -> tuple[list[float], list[float]]:
    scores = [dot(Q[i], K[j]) / math.sqrt(D) for j in range(len(K))]
    if causal:
        scores = [s if j <= i else float("-inf") for j, s in enumerate(scores)]
    weights = softmax(scores)
    out = [sum(w * V[j][k] for j, w in enumerate(weights)) for k in range(D)]
    return weights, out


# %% run
def main() -> None:
    print(f"causal mask: {'on' if CAUSAL else 'off'}")
    for i in range(len(Q)):
        w, o = attend(i, CAUSAL)
        print(f"token {i}: weights={[round(x, 2) for x in w]} -> out={[round(x, 2) for x in o]}")
    n = len(Q)
    print(f"\n{n} tokens -> {n * n} dot products. 4000 tokens -> {4000 * 4000:,}. That is the n^2.")


if __name__ == "__main__":
    main()
