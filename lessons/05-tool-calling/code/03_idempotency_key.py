"""Fact #3 of a successful tool call: the external system did it exactly once.

A side-effecting tool is retried after a timeout. Without an idempotency key
the transfer happens twice. With one, the second attempt is recognised and
the ledger stays correct. The key is derived from the tool call itself, so
the model does not have to know about it.

Run:  uv run python lessons/05-tool-calling/code/03_idempotency_key.py
      INJECT_TIMEOUT=1 uv run python lessons/05-tool-calling/code/03_idempotency_key.py
Expect: ledger always ends with exactly one transfer, even when the first
        attempt times out after the bank has already applied it.
"""

# %% imports
import asyncio
import hashlib
import json
import os

from aiapp import Message, ToolCall

INJECT_TIMEOUT = os.environ.get("INJECT_TIMEOUT") == "1"


# %% Bank
class Bank:
    """Stands in for any external system that supports idempotency keys."""

    def __init__(self) -> None:
        self.ledger: list[dict] = []
        self._seen: dict[str, dict] = {}

    async def transfer(self, *, idempotency_key: str, amount: int, to_account: str) -> dict:
        if idempotency_key in self._seen:
            return {**self._seen[idempotency_key], "replayed": True}
        entry = {"amount": amount, "to_account": to_account, "replayed": False}
        self.ledger.append(entry)
        self._seen[idempotency_key] = entry
        if INJECT_TIMEOUT and len(self.ledger) == 1:
            await asyncio.sleep(0.5)  # applied, but the reply is slow
        return entry


# %% idempotency_key
def idempotency_key(call: ToolCall) -> str:
    """Same call id + same canonical arguments => same key."""
    canonical = json.dumps(call.arguments, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(f"{call.id}:{call.name}:{canonical}".encode()).hexdigest()[:16]


# %% run_transfer
async def run_transfer(bank: Bank, call: ToolCall, *, attempts: int = 2, timeout: float = 0.1) -> Message:
    key = idempotency_key(call)
    for attempt in range(1, attempts + 1):
        try:
            result = await asyncio.wait_for(bank.transfer(idempotency_key=key, **call.arguments), timeout)
            print(f"attempt {attempt}: ok replayed={result['replayed']}")
            return Message(role="tool", tool_call_id=call.id, content=json.dumps(result))
        except TimeoutError:
            print(f"attempt {attempt}: timeout, retrying with the same key {key}")
    return Message(role="tool", tool_call_id=call.id, is_error=True, content="transfer status unknown after retries")


# %% main
async def main() -> None:
    bank = Bank()
    call = ToolCall(id="call_7f3a", name="transfer_money", arguments={"amount": 750, "to_account": "acc_jeff"})
    result = await run_transfer(bank, call)
    print(f"tool result: {result.content}")
    print(f"ledger has {len(bank.ledger)} transfer(s)")
    assert len(bank.ledger) == 1, "side effect happened more than once"


# %% run
if __name__ == "__main__":
    asyncio.run(main())
