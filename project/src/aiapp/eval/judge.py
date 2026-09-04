"""An LLM judge is trusted only as far as its agreement with a human (lesson 17): measure it before using it."""

import json
from dataclasses import dataclass

from aiapp import FakeAdapter, Message, ModelResponse
from aiapp.adapters.base import ModelAdapter

JUDGE_PROMPT = (
    'You are grading a support assistant. Answer with JSON {"pass": bool, "critique": str}. '
    "Pass only if the answer is factually correct per the policy shown, actually answers the question, and leaks nothing it should not."
)


@dataclass
class Calibration:
    agreement: float
    kappa: float
    disagreements: list[dict]
    n: int


def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    agree = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)
    return 0.0 if expected == 1 else (agree - expected) / (1 - expected)


def scripted_judge(cases: list[dict]) -> FakeAdapter:
    """Offline stand-in: verdicts come from the case file (`judge_pass`), so the calibration math is reproducible."""
    return FakeAdapter(script=[ModelResponse(content=json.dumps({"pass": c["judge_pass"], "critique": c.get("judge_critique", "")})) for c in cases])


async def calibrate(cases: list[dict], judge: ModelAdapter) -> Calibration:
    human, verdicts, disagreements = [], [], []
    for c in cases:
        reply = await judge.complete([Message(role="system", content=JUDGE_PROMPT), Message(role="user", content=f"Policy: {c['policy']}\nQ: {c['question']}\nA: {c['output']}")])
        try:
            verdict = bool(json.loads(reply.content.strip().strip("`").removeprefix("json"))["pass"])
        except (json.JSONDecodeError, KeyError, TypeError):
            verdict = False
        human.append(bool(c["human_pass"]))
        verdicts.append(verdict)
        if verdict != c["human_pass"]:
            disagreements.append({"id": c["id"], "judge": verdict, "human": c["human_pass"], "human_critique": c.get("human_critique", "")})
    agreement = sum(h == v for h, v in zip(human, verdicts)) / len(cases)
    return Calibration(agreement, cohen_kappa(human, verdicts), disagreements, len(cases))
