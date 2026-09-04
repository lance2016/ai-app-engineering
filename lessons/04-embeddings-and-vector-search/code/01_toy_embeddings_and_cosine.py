"""An embedding is a vector; similarity is an angle. Build the toy version.

This file turns sentences into fixed-size vectors with hashed bag-of-words,
then compares them with cosine similarity. It has no idea what words mean,
which is exactly the point: you will see where a lexical vector works and
where a learned embedding is needed.

Run:  uv run python lessons/04-embeddings-and-vector-search/code/01_toy_embeddings_and_cosine.py
Expect: a similarity table. Sentences sharing words score high; paraphrases
        with different words score near zero, which real embeddings would catch.
"""

# %% imports
import hashlib
import math
import re

DIM = 64


# %% embed
def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+|[一-鿿]", text.lower())


def embed(text: str, dim: int = DIM) -> list[float]:
    """Hash each token into one of `dim` buckets and count. Then L2-normalise."""
    vec = [0.0] * dim
    for tok in tokenize(text):
        bucket = int(hashlib.md5(tok.encode()).hexdigest(), 16) % dim
        vec[bucket] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


# %% cosine
def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


# %% run
def main() -> None:
    query = "how do I reset my password"
    candidates = [
        "steps to reset your password",  # shares words -> high
        "I forgot my login credentials, how can I get back in",  # paraphrase, no shared words -> low
        "how do I reset my router",  # shares words, different meaning -> high (false positive)
        "quarterly revenue grew by twelve percent",  # unrelated -> ~0
    ]
    q = embed(query)
    print(f"query: {query!r}\n")
    print(f"{'cosine':>7}  candidate")
    for text in candidates:
        print(f"{cosine(q, embed(text)):7.3f}  {text}")
    print("\nthe toy vector rewards shared words, not shared meaning. a learned embedding would rank")
    print("the paraphrase high and the router question low. that difference is what you pay an embedding model for.")


if __name__ == "__main__":
    main()
