"""How few parameters LoRA trains compared with full fine-tuning.

A d x d weight has d^2 parameters. LoRA freezes it and trains two thin
matrices A (d x r) and B (r x d) instead: r (d + d) parameters, with r in the
tens. Apply that to two projections per layer across 32 layers and the whole
model trains a few million parameters instead of billions.

Run:  uv run python prerequisites/llm-foundations/05-training-and-alignment/code/02_lora_param_count.py
Expect: per-rank comparison and the whole-model number for rank 16.
"""


# %% count
def lora_params(d_in: int, d_out: int, rank: int) -> int:
    return rank * (d_in + d_out)


def full_params(d_in: int, d_out: int) -> int:
    return d_in * d_out


# %% run
def main() -> None:
    d = 4096
    for r in [4, 8, 16, 64]:
        lora, full = lora_params(d, d, r), full_params(d, d)
        print(f"rank {r:>2}: LoRA {lora / 1e6:.2f}M vs full {full / 1e6:.1f}M  ({lora / full * 100:.2f}%)")
    layers, targets = 32, 2  # LoRA on the Q and V projections of every layer
    print(f"\nwhole model, rank 16: {layers * targets * lora_params(d, d, 16) / 1e6:.1f}M trainable params")
    print("vs 7B full finetune:   ~6600M")


if __name__ == "__main__":
    main()
