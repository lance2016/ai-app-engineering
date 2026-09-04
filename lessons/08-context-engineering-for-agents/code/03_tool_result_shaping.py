"""Tool results are context too. Shape them before they hit the window.

A query returns 500 rows. Dropping all of it into the context burns tokens and
buries the signal. The runtime stores the full result by reference, injects a
compact view (schema, count, head, tail) and offers a tool to fetch more. This
is the "just in time" pattern: keep identifiers in context, load data on demand.

Run:  uv run python lessons/08-context-engineering-for-agents/code/03_tool_result_shaping.py
      INJECT_RAW=1 uv run python lessons/08-context-engineering-for-agents/code/03_tool_result_shaping.py
Expect: shaped result is a few hundred tokens with a result id; raw injection is
        tens of thousands of tokens for the same information.
"""

# %% imports
import json
import os
import uuid

from aiapp import Message, ToolCall

INJECT_RAW = os.environ.get("INJECT_RAW") == "1"
RESULT_STORE: dict[str, list[dict]] = {}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# %% big_tool
def query_orders(args: dict) -> list[dict]:
    return [{"order_id": f"o_{i:04d}", "customer": f"cust_{i % 37}", "amount": round(19.99 + i * 1.37, 2), "status": ["shipped", "pending", "refunded"][i % 3]} for i in range(500)]


# %% shaping
def shape(rows: list[dict], *, head: int = 3, tail: int = 2) -> str:
    """Compact view: what it is, how big, a sample, and how to get the rest."""
    ref = f"res_{uuid.uuid4().hex[:6]}"
    RESULT_STORE[ref] = rows
    by_status: dict[str, int] = {}
    for r in rows:
        by_status[r["status"]] = by_status.get(r["status"], 0) + 1
    return json.dumps({
        "result_id": ref,
        "row_count": len(rows),
        "columns": list(rows[0].keys()),
        "status_counts": by_status,
        "head": rows[:head],
        "tail": rows[-tail:],
        "hint": f"call fetch_rows(result_id='{ref}', offset, limit) for more",
    })


def fetch_rows(args: dict) -> str:
    rows = RESULT_STORE[args["result_id"]]
    return json.dumps(rows[args["offset"]: args["offset"] + args["limit"]])


# %% run
def main() -> None:
    call = ToolCall(id="c1", name="query_orders", arguments={"since": "2026-08-01"})
    rows = query_orders(call.arguments)
    content = json.dumps(rows) if INJECT_RAW else shape(rows)
    result = Message(role="tool", tool_call_id=call.id, content=content)
    print(f"mode={'raw' if INJECT_RAW else 'shaped'} tokens~{estimate_tokens(result.content)} chars={len(result.content)}")
    print(result.content[:300] + ("..." if len(result.content) > 300 else ""))
    if not INJECT_RAW:
        ref = json.loads(content)["result_id"]
        page = fetch_rows({"result_id": ref, "offset": 100, "limit": 2})
        print(f"\nmodel asks for more -> fetch_rows(offset=100, limit=2): {page}")


if __name__ == "__main__":
    main()
