"""A byte-pair-encoding tokenizer in 60 lines, so "token" stops being abstract.

Real tokenizers (GPT-2's, Qwen's, DeepSeek's) are this algorithm trained on
far more text with far more merges. The consequences you will feel in every
lesson are visible already: tokens are not words, common strings compress
well, rare strings and non-Latin scripts do not.

Run:  uv run python lessons/01-how-llms-work/code/01_bpe_tokenizer_toy.py
      SHOW_MERGES=1 uv run python lessons/01-how-llms-work/code/01_bpe_tokenizer_toy.py
Expect: the learned merges, then several strings with their token counts and
        the bytes-per-token ratio. English compresses, Chinese barely does.
"""

# %% imports
import os
from collections import Counter

SHOW_MERGES = os.environ.get("SHOW_MERGES") == "1"

CORPUS = (
    "the model predicts the next token. the next token depends on the context. "
    "tokens are not words. the tokenizer learns merges from the training text. "
    "the model sees tokens, not characters."
)


# %% train
def train_bpe(text: str, num_merges: int) -> list[tuple[int, int]]:
    """Repeatedly merge the most frequent adjacent pair of symbols."""
    ids = list(text.encode("utf-8"))
    merges: list[tuple[int, int]] = []
    next_id = 256
    for _ in range(num_merges):
        pairs = Counter(zip(ids, ids[1:]))
        if not pairs:
            break
        pair, count = pairs.most_common(1)[0]
        if count < 2:
            break
        merges.append(pair)
        ids = _apply_merge(ids, pair, next_id)
        next_id += 1
    return merges


def _apply_merge(ids: list[int], pair: tuple[int, int], new_id: int) -> list[int]:
    out: list[int] = []
    i = 0
    while i < len(ids):
        if i + 1 < len(ids) and (ids[i], ids[i + 1]) == pair:
            out.append(new_id)
            i += 2
        else:
            out.append(ids[i])
            i += 1
    return out


# %% encode_decode
def encode(text: str, merges: list[tuple[int, int]]) -> list[int]:
    ids = list(text.encode("utf-8"))
    for new_id, pair in enumerate(merges, start=256):
        ids = _apply_merge(ids, pair, new_id)
    return ids


def decode(ids: list[int], merges: list[tuple[int, int]]) -> str:
    vocab: dict[int, bytes] = {i: bytes([i]) for i in range(256)}
    for new_id, (a, b) in enumerate(merges, start=256):
        vocab[new_id] = vocab[a] + vocab[b]
    return b"".join(vocab[i] for i in ids).decode("utf-8", errors="replace")


# %% run
def main() -> None:
    merges = train_bpe(CORPUS, num_merges=40)
    print(f"learned {len(merges)} merges from {len(CORPUS.encode())} bytes of text")
    if SHOW_MERGES:
        vocab = {i: bytes([i]) for i in range(256)}
        for new_id, (a, b) in enumerate(merges, start=256):
            vocab[new_id] = vocab[a] + vocab[b]
            print(f"  merge {new_id}: {vocab[a]!r} + {vocab[b]!r} -> {vocab[new_id]!r}")
    samples = [
        "the next token",  # seen often in the corpus
        "the quick brown fox",  # english, but unseen words
        "下一个词是什么",  # chinese: every character is 3 bytes and never merged
        "x7Qz#9",  # gibberish
    ]
    print(f"\n{'text':24} {'bytes':>5} {'tokens':>6} {'bytes/token':>11}")
    for text in samples:
        ids = encode(text, merges)
        assert decode(ids, merges) == text
        print(f"{text:24} {len(text.encode()):5} {len(ids):6} {len(text.encode()) / len(ids):11.2f}")
    print("\nthe model never sees characters; it sees these ids. token count is what you pay for.")


if __name__ == "__main__":
    main()
