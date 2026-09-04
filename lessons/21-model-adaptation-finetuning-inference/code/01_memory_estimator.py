"""How much GPU memory does serving this model take? Two terms, both matter.

Weights = parameters x bytes per parameter (fp16 2, int8 1, int4 0.5).
KV cache = 2 x layers x kv_heads x head_dim x bytes x seq_len x batch.
People remember the first term and get surprised by the second at 32k context.
Grouped-query attention (fewer kv_heads) is the reason 8B models can serve
long contexts at all.

Run:  uv run python lessons/21-model-adaptation-finetuning-inference/code/01_memory_estimator.py
      INJECT_IGNORE_KV=1 uv run python lessons/21-model-adaptation-finetuning-inference/code/01_memory_estimator.py
Expect: a table of weights + KV cache per precision, batch and context. With
        the injection the KV term is dropped and the estimate looks affordable when it is not.
"""

# %% imports
import os
from dataclasses import dataclass

INJECT_IGNORE_KV = os.environ.get("INJECT_IGNORE_KV") == "1"
GB = 1024**3


# %% model_shapes
@dataclass(frozen=True)
class ModelShape:
    """Architecture numbers. Check the model's config.json; these are the commonly published values."""

    name: str
    params_b: float
    layers: int
    kv_heads: int
    head_dim: int


SHAPES = [
    ModelShape("7B  GQA kv=4", 7.6, 28, 4, 128),
    ModelShape("8B  GQA kv=8", 8.0, 32, 8, 128),
    ModelShape("70B GQA kv=8", 70.0, 80, 8, 128),
    ModelShape("7B  MHA kv=32", 7.0, 32, 32, 128),  # what the same model would cost without GQA
]
BYTES = {"fp16/bf16": 2.0, "int8": 1.0, "int4": 0.5}


# %% estimators
def weights_bytes(m: ModelShape, bytes_per_param: float) -> float:
    return m.params_b * 1e9 * bytes_per_param


def kv_cache_bytes(m: ModelShape, *, seq_len: int, batch: int, bytes_per_value: float = 2.0) -> float:
    if INJECT_IGNORE_KV:
        return 0.0
    return 2 * m.layers * m.kv_heads * m.head_dim * bytes_per_value * seq_len * batch


# %% run
def main() -> None:
    print(f"{'model / precision':26} {'weights':>9} {'kv 1x8k':>9} {'kv 8x32k':>10} {'total 8x32k':>12}")
    for m in SHAPES:
        for prec, b in BYTES.items():
            w = weights_bytes(m, b)
            kv_small = kv_cache_bytes(m, seq_len=8_192, batch=1)
            kv_big = kv_cache_bytes(m, seq_len=32_768, batch=8)
            print(f"{m.name + '  ' + prec:26} {w / GB:8.1f}G {kv_small / GB:8.1f}G {kv_big / GB:9.1f}G {(w + kv_big) / GB:11.1f}G")
        print()
    print("KV cache is stored in fp16 even when weights are int4 (unless the engine quantises the cache too).")
    if INJECT_IGNORE_KV:
        print("!! KV term ignored: the 70B int4 row now looks like it fits an 80G card at batch 8 x 32k. It does not.")


if __name__ == "__main__":
    main()
