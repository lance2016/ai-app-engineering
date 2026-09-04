"""Where the 7 billion parameters live, and how many gigabytes they weigh.

Per layer: four attention projections (4 d^2) plus a two-layer feed-forward
(8 d^2 with the usual 4x expansion). Plus the token embedding table. Real
models use SwiGLU and slightly different ratios, so expect a rounding gap.

Run:  uv run python prerequisites/llm-foundations/03-attention-and-transformer/code/02_gpt_param_count.py
Expect: ~6.6B total for a 32-layer, d=4096, 32k-vocab model and its size in fp16 / int8 / int4.
"""


# %% count
def gpt_params(n_layers: int, d_model: int, vocab: int, ffn_mult: int = 4, tie_embeddings: bool = True) -> tuple[int, int, int]:
    attention = 4 * d_model * d_model  # Q, K, V, O projections
    ffn = 2 * d_model * (ffn_mult * d_model)  # d -> 4d -> d
    per_layer = attention + ffn
    embedding = vocab * d_model
    head = 0 if tie_embeddings else vocab * d_model
    total = n_layers * per_layer + embedding + head
    return total, per_layer, embedding


# %% run
def main() -> None:
    total, per_layer, emb = gpt_params(n_layers=32, d_model=4096, vocab=32000)
    print(f"per layer: {per_layer / 1e6:.0f}M, embedding: {emb / 1e6:.0f}M, total: {total / 1e9:.2f}B")
    for bytes_per_param, name in [(2, "fp16"), (1, "int8"), (0.5, "int4")]:
        print(f"  weights in {name}: {total * bytes_per_param / 1e9:.1f} GB")


if __name__ == "__main__":
    main()
