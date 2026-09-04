"""A language model that has never seen a fact, only which word tends to follow which.

Train a bigram model on a handful of sentences and let it generate. The
output is fluent-ish and confidently wrong, because fluency and truth are
different things: the model reproduces statistical patterns, it does not look
anything up. Scale this to trillions of tokens and you get an LLM's strengths
and its hallucinations from the same mechanism.

Run:  uv run python prerequisites/llm-foundations/00-what-an-llm-is/code/01_bigram_lm.py
      SEED=7 uv run python prerequisites/llm-foundations/00-what-an-llm-is/code/01_bigram_lm.py
Expect: five generated sentences. Some are true, some blend facts from
        different sentences. The model cannot tell which is which.
"""

# %% imports
import os
import random
from collections import Counter, defaultdict

SEED = int(os.environ.get("SEED", "1"))

CORPUS = [
    "paris is the capital of france",
    "berlin is the capital of germany",
    "tokyo is the capital of japan",
    "the seine flows through paris",
    "the spree flows through berlin",
    "france borders germany",
    "japan is an island nation",
]


# %% train
def train(sentences: list[str]) -> dict[str, Counter]:
    """For every word, count what followed it. That is the entire model."""
    follows: dict[str, Counter] = defaultdict(Counter)
    for s in sentences:
        words = ["<s>", *s.split(), "</s>"]
        for a, b in zip(words, words[1:]):
            follows[a][b] += 1
    return follows


# %% generate
def generate(model: dict[str, Counter], rng: random.Random, max_len: int = 12) -> str:
    word = "<s>"
    out: list[str] = []
    for _ in range(max_len):
        nxt = model[word]
        word = rng.choices(list(nxt), weights=list(nxt.values()))[0]
        if word == "</s>":
            break
        out.append(word)
    return " ".join(out)


# %% run
def main() -> None:
    model = train(CORPUS)
    rng = random.Random(SEED)
    print("what follows 'the'? ->", dict(model["the"]))
    print("what follows 'capital'? ->", dict(model["capital"]), "\n")
    for i in range(5):
        sentence = generate(model, rng)
        verdict = "in corpus" if sentence in CORPUS else "NOT in corpus (plausible, unverified)"
        print(f"{i + 1}. {sentence:40} [{verdict}]")
    print("\nnothing here stores 'paris -> france' as a fact. it stores 'of' is often followed by 'france'.")
    print("when you need facts, give them to the model in the context (lesson 13) or look them up with a tool (lesson 05).")


if __name__ == "__main__":
    main()
