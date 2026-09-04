"""Evaluator-optimizer: one model drafts, another critiques, loop until pass or budget.

Works when the evaluation criteria are explicit enough that a critic can score
against them. The loop is bounded by rounds, and the evaluator's verdict is
structured so the runtime, not the model, decides whether to continue.

Run:  uv run python lessons/09-workflow-vs-agent/code/05_evaluator_optimizer.py
      INJECT_NEVER_PASSES=1 uv run python lessons/09-workflow-vs-agent/code/05_evaluator_optimizer.py
Expect: pass on round 2; with injection the loop stops at the round cap and
        returns the best attempt so far, flagged as not passing.
"""

# %% imports
import asyncio
import json
import os

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_NEVER_PASSES = os.environ.get("INJECT_NEVER_PASSES") == "1"
MAX_ROUNDS = 3


# %% loop
async def refine(generator: FakeAdapter, evaluator: FakeAdapter, task: str) -> tuple[str, bool]:
    feedback = ""
    best, best_score = "", -1
    for round_no in range(1, MAX_ROUNDS + 1):
        draft = (await generator.complete([Message(role="user", content=f"{task}\nFeedback: {feedback or 'none'}")])).content
        verdict = json.loads((await evaluator.complete([Message(role="user", content=f"Score 0-10 and give feedback as JSON: {draft}")])).content)
        print(f"round {round_no}: score={verdict['score']} feedback={verdict['feedback']!r}")
        if verdict["score"] > best_score:
            best, best_score = draft, verdict["score"]
        if verdict["score"] >= 8:
            return best, True
        feedback = verdict["feedback"]
    return best, False


# %% run
async def main() -> None:
    generator = FakeAdapter(script=[ModelResponse(content=f"translation v{i}") for i in range(1, 4)])
    scores = [5, 6, 6] if INJECT_NEVER_PASSES else [5, 9]
    evaluator = FakeAdapter(script=[ModelResponse(content=json.dumps({"score": s, "feedback": "tone too formal" if s < 8 else "good"})) for s in scores])
    result, passed = await refine(generator, evaluator, "Translate the poem.")
    print(f"result={result!r} passed={passed}")


if __name__ == "__main__":
    asyncio.run(main())
