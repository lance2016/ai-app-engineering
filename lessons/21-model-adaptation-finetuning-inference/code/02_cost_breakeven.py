"""Hosted API or your own GPU? Compute the break-even instead of arguing.

Self-hosting has a fixed hourly cost whether or not tokens flow; the API bills
per token. Break-even is the monthly volume where the two lines cross, and it
moves a lot with utilisation. Every input is an assumption you should replace
with your own numbers and today's prices.

Run:  uv run python lessons/21-model-adaptation-finetuning-inference/code/02_cost_breakeven.py
      UTILISATION=0.2 uv run python lessons/21-model-adaptation-finetuning-inference/code/02_cost_breakeven.py
Expect: cost per 1M tokens for both options and the break-even monthly volume,
        plus how it shifts when the GPU sits idle most of the time.
"""

# %% imports
import os

# %% assumptions
# ILLUSTRATIVE, dated 2026-09-04. Replace with your provider's price sheet and your cloud's GPU rate.
API_USD_PER_M_IN = 0.30
API_USD_PER_M_OUT = 1.20
GPU_USD_PER_HOUR = 2.50  # one 80G card, on-demand
GPU_TOKENS_PER_SEC = 1_500  # aggregate decode throughput at healthy batch size for a 7B-class model
UTILISATION = float(os.environ.get("UTILISATION", "0.6"))  # share of the hour the GPU is actually generating
HOURS_PER_MONTH = 730
OUTPUT_SHARE = 0.25  # of total tokens; the rest are (cheaper) input tokens


# %% per_million
def api_cost_per_m(output_share: float) -> float:
    return API_USD_PER_M_IN * (1 - output_share) + API_USD_PER_M_OUT * output_share


def selfhost_cost_per_m(utilisation: float) -> float:
    tokens_per_hour = GPU_TOKENS_PER_SEC * 3600 * utilisation
    return GPU_USD_PER_HOUR / tokens_per_hour * 1_000_000


# %% breakeven
def breakeven_tokens_per_month() -> float:
    """Volume where paying for the GPU all month equals paying the API per token."""
    monthly_gpu = GPU_USD_PER_HOUR * HOURS_PER_MONTH
    return monthly_gpu / api_cost_per_m(OUTPUT_SHARE) * 1_000_000


# %% run
def main() -> None:
    api = api_cost_per_m(OUTPUT_SHARE)
    own = selfhost_cost_per_m(UTILISATION)
    be = breakeven_tokens_per_month()
    capacity = GPU_TOKENS_PER_SEC * 3600 * HOURS_PER_MONTH * UTILISATION
    print(f"API            : ${api:.3f} per 1M tokens (blended, {OUTPUT_SHARE:.0%} output)")
    print(f"self-hosted    : ${own:.3f} per 1M tokens at {UTILISATION:.0%} utilisation")
    print(f"break-even     : {be / 1e6:,.0f}M tokens/month (GPU costs ${GPU_USD_PER_HOUR * HOURS_PER_MONTH:,.0f}/month)")
    print(f"GPU capacity   : {capacity / 1e6:,.0f}M tokens/month at that utilisation")
    verdict = "self-hosting is cheaper per token" if own < api else "the API is cheaper per token"
    print(f"verdict        : {verdict}; and this ignores engineers, on-call, upgrades and the second GPU for failover")


if __name__ == "__main__":
    main()
