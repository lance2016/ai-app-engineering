"""Two things every production call needs and no SDK does for you: a retry
policy you understand and a cost ledger you can query.

Rate limits and timeouts are normal; retry them with backoff and a cap. Bad
requests are not retried at all. Every response's usage is priced and
recorded, so "how much did this conversation cost" is a lookup, not a guess.

Run:  uv run python lessons/02-model-api-structured-output-streaming/code/04_retry_and_cost.py
      INJECT_RATE_LIMIT=1 uv run python lessons/02-model-api-structured-output-streaming/code/04_retry_and_cost.py
Expect: three calls priced and totalled. With injection the first call is
        rate-limited twice, retried with growing delays, then succeeds.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass, field

from aiapp import FakeAdapter, Message, ModelResponse, Usage

INJECT_RATE_LIMIT = os.environ.get("INJECT_RATE_LIMIT") == "1"

# Example prices per 1M tokens. Real numbers change; read them from config, not code.
PRICES = {"fake": (0.27, 1.10)}  # (input, output) USD per 1M, roughly DeepSeek-chat's public list on 2026-09-04


class RateLimited(Exception):
    pass


class BadRequest(Exception):
    pass


# %% flaky_adapter
class FlakyAdapter(FakeAdapter):
    """Raises RateLimited on the first N calls, then behaves."""

    def __init__(self, script, *, fail_first: int):
        super().__init__(script)
        self._fail_first = fail_first

    async def complete(self, messages, tools=None):
        if self._fail_first > 0:
            self._fail_first -= 1
            raise RateLimited("429 too many requests")
        return await super().complete(messages, tools)


# %% retry_policy
async def complete_with_retry(model, messages, *, max_attempts: int = 4, base_delay: float = 0.05) -> ModelResponse:
    for attempt in range(1, max_attempts + 1):
        try:
            return await model.complete(messages)
        except RateLimited as exc:
            if attempt == max_attempts:
                raise
            delay = base_delay * 2 ** (attempt - 1)
            print(f"  attempt {attempt}: {exc}; retrying in {delay:.2f}s")
            await asyncio.sleep(delay)
        except BadRequest:
            raise  # our fault; retrying the same request cannot help
    raise AssertionError("unreachable")


# %% cost_ledger
@dataclass
class CostLedger:
    entries: list[tuple[str, Usage, float]] = field(default_factory=list)

    def record(self, label: str, usage: Usage, provider: str) -> float:
        price_in, price_out = PRICES[provider]
        cost = usage.input_tokens / 1e6 * price_in + usage.output_tokens / 1e6 * price_out
        self.entries.append((label, usage, cost))
        return cost

    @property
    def total(self) -> float:
        return sum(c for _, _, c in self.entries)


# %% run
async def main() -> None:
    script = [ModelResponse(content="Answer one."), ModelResponse(content="Answer two, a bit longer than the first."), ModelResponse(content="Three.")]
    model = FlakyAdapter(script, fail_first=2 if INJECT_RATE_LIMIT else 0)
    ledger = CostLedger()
    for i in range(3):
        reply = await complete_with_retry(model, [Message(role="user", content=f"question {i}")])
        cost = ledger.record(f"call {i}", reply.usage, model.name)
        print(f"call {i}: in={reply.usage.input_tokens} out={reply.usage.output_tokens} cost=${cost:.8f}")
    print(f"\nconversation total: ${ledger.total:.8f} over {len(ledger.entries)} calls")
    print("tiny numbers per call; multiply by users and turns before deciding anything is cheap.")


if __name__ == "__main__":
    asyncio.run(main())
