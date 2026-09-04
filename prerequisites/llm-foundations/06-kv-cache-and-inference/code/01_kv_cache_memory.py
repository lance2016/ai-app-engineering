"""KV cache memory: the term people forget when sizing a GPU for long contexts.

Bytes = 2 (K and V) x layers x kv_heads x head_dim x bytes_per_value x seq_len.
Grouped-query attention shrinks kv_heads and therefore the cache; that is
the difference between "supports 128k" and "can afford 128k".

Run:  uv run python prerequisites/llm-foundations/06-kv-cache-and-inference/code/01_kv_cache_memory.py
Expect: per-token KB and per-context GB for a 7B with and without GQA, then
        how many concurrent 32k requests fit next to int4 weights on a 24GB card.
"""


# %% formula
def kv_cache_bytes(n_layers: int, n_kv_heads: int, head_dim: int, seq_len: int, bytes_per_value: float = 2) -> float:
    return 2 * n_layers * n_kv_heads * head_dim * bytes_per_value * seq_len


def show(name: str, n_layers: int, n_heads: int, n_kv_heads: int, head_dim: int) -> None:
    per_token = kv_cache_bytes(n_layers, n_kv_heads, head_dim, 1)
    print(f"{name}: {per_token / 1024:.0f} KB per token  (GQA ratio {n_heads}/{n_kv_heads})")
    for seq in [4_096, 32_768, 128_000]:
        print(f"   {seq:>7} tokens -> {kv_cache_bytes(n_layers, n_kv_heads, head_dim, seq) / 1e9:5.1f} GB")


# %% run
def main() -> None:
    show("7B, no GQA", n_layers=32, n_heads=32, n_kv_heads=32, head_dim=128)
    show("7B, GQA-8  ", n_layers=32, n_heads=32, n_kv_heads=8, head_dim=128)
    free = 24 - 3.5  # 24GB card minus int4 weights
    per_req = kv_cache_bytes(32, 8, 128, 32_768) / 1e9
    print(f"\n24GB card, int4 weights: ~{free / per_req:.1f} concurrent 32k requests (fp16 KV cache)")
    print(f"with int8 KV cache:      ~{free / (per_req / 2):.1f}")


if __name__ == "__main__":
    main()
