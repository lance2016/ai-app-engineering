"""Test the model on your own task before trusting it: a tiny probe suite.

Benchmarks tell you how a model did on someone else's tasks. A probe is a
prompt plus a deterministic checker for one capability you rely on: valid
JSON, exact arithmetic, counting, following a length instruction, admitting
it does not know. Run the same probes against every candidate, and again
after every model upgrade.

Run:  uv run python lessons/01-how-llms-work/code/02_capability_probe.py
      INJECT_TRUST_SELF_REPORT=1 uv run python lessons/01-how-llms-work/code/02_capability_probe.py
      MODEL_PROVIDER=deepseek uv run python lessons/01-how-llms-work/code/02_capability_probe.py
Expect: a pass/fail table. The fake adapter replays scripted answers, so
        offline the *shape* of the report is the point; with a real model the
        numbers are. With the injection every checker is replaced by "did the
        model say it was confident" and everything passes, which is the bug.
"""

# %% imports
import asyncio
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass

from aiapp import FakeAdapter, Message, ModelAdapter, ModelResponse, get_adapter

INJECT_TRUST_SELF_REPORT = os.environ.get("INJECT_TRUST_SELF_REPORT") == "1"


# %% probes
@dataclass(frozen=True)
class Probe:
    capability: str
    prompt: str
    check: Callable[[str], bool]
    why_it_matters: str


def is_json_with_keys(*keys: str) -> Callable[[str], bool]:
    def check(answer: str) -> bool:
        try:
            data = json.loads(answer.strip().strip("`").removeprefix("json").strip())
        except json.JSONDecodeError:
            return False
        return isinstance(data, dict) and all(k in data for k in keys)

    return check


def contains_number(expected: int) -> Callable[[str], bool]:
    return lambda answer: str(expected) in re.findall(r"\d+", answer)


def exactly_n_bullets(n: int) -> Callable[[str], bool]:
    return lambda answer: sum(1 for line in answer.splitlines() if line.strip().startswith("-")) == n


def admits_uncertainty(answer: str) -> bool:
    hedges = ("不知道", "无法", "没有找到", "不确定", "not sure", "cannot", "can't", "don't know", "no information", "not aware")
    return any(h in answer.lower() for h in hedges)


PROBES = [
    Probe("json_format", 'Return only JSON with keys "city" and "country" for the capital of France.', is_json_with_keys("city", "country"), "structured output parsing (lesson 02)"),
    Probe("arithmetic", "What is 37 * 43? Answer with the number only.", contains_number(1591), "anything numeric should go through a tool instead (lesson 05)"),
    Probe("counting", "How many times does the letter r appear in 'strawberry'? Number only.", contains_number(3), "tokens are not letters (F01)"),
    Probe("instruction_following", "List exactly three benefits of unit tests as markdown bullets starting with '-'. Nothing else.", exactly_n_bullets(3), "prompt constraints are suggestions, not guarantees (lesson 03)"),
    Probe("admits_unknown", "Describe the three endpoints of the Zorblax-9 public API.", admits_uncertainty, "a fluent answer about a thing that does not exist is a hallucination (F00)"),
]

# What a mediocre model might say. Every answer *claims* confidence.
FAKE_ANSWERS = [
    '{"city": "Paris", "country": "France"}',
    "1591. I'm confident.",
    "There are 2 r's in strawberry. I'm confident.",
    "- Catch regressions early\n- Document behaviour\n- Enable refactoring\n- Improve design\nI'm confident these are right.",
    "The Zorblax-9 API exposes /devices, /telemetry and /commands. I'm confident.",
]


# %% run
def self_report_check(answer: str) -> bool:
    return "confident" in answer.lower()


async def run_probes(model: ModelAdapter) -> None:
    passed = 0
    failed: list[Probe] = []
    print(f"model: {model.name}   checker: {'model self-report (INJECTED)' if INJECT_TRUST_SELF_REPORT else 'deterministic'}\n")
    print(f"{'capability':22} {'result':6} answer (first 60 chars)")
    for probe in PROBES:
        reply = await model.complete([Message(role="user", content=probe.prompt)])
        check = self_report_check if INJECT_TRUST_SELF_REPORT else probe.check
        ok = check(reply.content)
        passed += ok
        if not ok:
            failed.append(probe)
        first_line = reply.content.strip().splitlines()[0] if reply.content.strip() else ""
        print(f"{probe.capability:22} {'pass' if ok else 'FAIL':6} {first_line[:60]}")
    print(f"\n{passed}/{len(PROBES)} passed")
    if INJECT_TRUST_SELF_REPORT:
        print("everything passed because we asked the model whether it was right. It always is, in its own opinion.")
    else:
        print("what each failure means for the application:")
        for p in failed:
            print(f"  - {p.capability}: {p.why_it_matters}")


def build_model() -> ModelAdapter:
    provider = os.environ.get("MODEL_PROVIDER", "fake").lower()
    if provider == "fake":
        return FakeAdapter(script=[ModelResponse(content=a) for a in FAKE_ANSWERS])
    return get_adapter(provider)


if __name__ == "__main__":
    asyncio.run(run_probes(build_model()))
