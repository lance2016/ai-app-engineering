"""Changing a prompt is a code change. Gate it with a golden set.

A small set of inputs with expected labels runs against the prompt. With the
fake adapter the run is deterministic and shows the harness; set a real
provider to see whether v2 actually beats v1. Lesson 17 grows this into a
proper evaluation.

Run:  uv run python lessons/03-prompt-engineering/code/02_prompt_regression_test.py
      INJECT_REGRESSION=1 uv run python lessons/03-prompt-engineering/code/02_prompt_regression_test.py
      MODEL_PROVIDER=deepseek uv run python lessons/03-prompt-engineering/code/02_prompt_regression_test.py
Expect: an accuracy per prompt version and a pass/fail gate. Injection makes
        v2 misclassify one case, yet v2 still ties v1 and the `>=` gate lets the
        tie through. That is deliberate: see the lesson's "常见错误" and exercise 2,
        which tightens the gate.
"""

# %% imports
import asyncio
import os

from aiapp import FakeAdapter, Message, ModelResponse, get_adapter

INJECT_REGRESSION = os.environ.get("INJECT_REGRESSION") == "1"
LABELS = ("billing", "technical", "other")

GOLDEN = [
    ("I was charged twice this month", "billing"),
    ("The app crashes when I open settings", "technical"),
    ("Do you have a student discount?", "billing"),
    ("Sync stopped working after the update", "technical"),
    ("What are your office hours?", "other"),
]

PROMPTS = {
    "v1": "Classify the support message into one of: billing, technical, other. Reply with the label only.",
    "v2": (
        "You route support messages. Labels:\n"
        "- billing: charges, invoices, discounts, refunds\n"
        "- technical: crashes, bugs, sync, login problems\n"
        "- other: anything else\n"
        "Reply with exactly one label in lowercase, nothing else."
    ),
}


# %% classify
def normalise(text: str) -> str:
    text = text.strip().lower().strip(".")
    return text if text in LABELS else "other"


async def classify(model, system: str, message: str) -> str:
    reply = await model.complete([Message(role="system", content=system), Message(role="user", content=message)])
    return normalise(reply.content)


# %% harness
def fake_for(version: str) -> FakeAdapter:
    """Scripted answers standing in for a real model; v1 gets one case wrong, v2 gets all right unless injected."""
    answers = [label for _, label in GOLDEN]
    if version == "v1":
        answers[2] = "other"  # v1 misses that discounts are billing
    if version == "v2" and INJECT_REGRESSION:
        answers[3] = "other"
    return FakeAdapter(script=[ModelResponse(content=a) for a in answers])


async def evaluate(version: str) -> float:
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    model = fake_for(version) if provider == "fake" else get_adapter(provider)
    correct = 0
    for message, expected in GOLDEN:
        got = await classify(model, PROMPTS[version], message)
        mark = "ok " if got == expected else "MISS"
        correct += got == expected
        print(f"  [{mark}] {version} {message[:40]:40} -> {got:9} (want {expected})")
    return correct / len(GOLDEN)


# %% run
async def main() -> None:
    scores = {}
    for version in PROMPTS:
        print(f"== {version} ==")
        scores[version] = await evaluate(version)
    print(f"\naccuracy: {scores}")
    gate = scores["v2"] >= scores["v1"] and scores["v2"] >= 0.8
    print("gate:", "PASS, v2 may ship" if gate else "FAIL, v2 regressed; keep v1")
    print("five cases is a smoke test, not an evaluation. lesson 17 covers how many you need and how to slice them.")


if __name__ == "__main__":
    asyncio.run(main())
