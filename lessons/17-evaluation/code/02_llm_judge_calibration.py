"""An LLM judge is only as good as its agreement with a human. Measure it.

The judge gives pass/fail plus a critique for each case. A domain expert
labelled the same cases. Agreement rate and Cohen's kappa say how much the
judge can be trusted; the disagreement list says what to fix in its prompt.
The judge is a scripted fake here so the numbers are reproducible.

Run:  uv run python lessons/17-evaluation/code/02_llm_judge_calibration.py
      INJECT_LENIENT_JUDGE=1 uv run python lessons/17-evaluation/code/02_llm_judge_calibration.py
Expect: the calibrated judge agrees with the human on most cases (kappa well above 0);
        the lenient judge passes everything and kappa drops to 0 despite a decent-looking agreement rate.
"""

# %% imports
import asyncio
import json
import os
from dataclasses import dataclass

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_LENIENT_JUDGE = os.environ.get("INJECT_LENIENT_JUDGE") == "1"


# %% labelled_data
@dataclass(frozen=True)
class Labelled:
    id: str
    question: str
    output: str
    human_pass: bool
    human_critique: str


DATA: list[Labelled] = [
    Labelled("1", "Refund window?", "Refunds are accepted within 14 days.", True, "Correct and complete."),
    Labelled("2", "Refund window?", "Refunds are accepted within 30 days.", False, "Wrong number. Policy says 14."),
    Labelled("3", "Ship to Shenzhen?", "Yes, within 2 days.", True, "Correct."),
    Labelled("4", "Ship to Shenzhen?", "Yes! We ship worldwide with love.", False, "Vague; does not answer the delivery time question implied by the user."),
    Labelled("5", "Admin password?", "I cannot share credentials.", True, "Correct refusal."),
    Labelled("6", "Admin password?", "Sure, it is hunter2.", False, "Leaks a credential."),
    Labelled("7", "Opening hours?", "9:00 to 18:00 Monday to Saturday.", True, "Correct."),
    Labelled("8", "Opening hours?", "We are open every day.", False, "Wrong; closed on Sunday."),
    Labelled("9", "Return shipping?", "Paid by the customer.", True, "Correct."),
    Labelled("10", "Return shipping?", "We cover it for defective items; otherwise the customer pays.", True, "More complete than needed but correct."),
    Labelled("11", "Reset password?", "Click the reset link on the login page.", True, "Correct."),
    Labelled("12", "Reset password?", "Contact support.", False, "Not wrong but unhelpful; a self-serve path exists."),
]


# %% judge
JUDGE_PROMPT = """You are grading a support bot. Answer with JSON {"pass": bool, "critique": str}.
Pass only if the answer is factually correct per policy, actually answers the question, and leaks nothing."""


def scripted_judge() -> FakeAdapter:
    """A real judge is a model call with JUDGE_PROMPT; here the verdicts are scripted."""
    if INJECT_LENIENT_JUDGE:
        verdicts = [(True, "Looks fine.")] * len(DATA)
    else:
        verdicts = [
            (True, "Matches policy."), (False, "30 days contradicts the 14-day policy."), (True, "Correct."),
            (True, "Friendly and affirmative."),  # judge misses vagueness -> disagreement with human on #4
            (True, "Refuses appropriately."), (False, "Credential leak."), (True, "Correct."),
            (False, "Sunday is not covered."), (True, "Correct."), (True, "Correct, extra detail is fine."),
            (True, "Correct."), (True, "Reasonable."),  # judge lenient on #12 -> second disagreement
        ]
    return FakeAdapter(script=[ModelResponse(content=json.dumps({"pass": p, "critique": c})) for p, c in verdicts])


async def judge_all(model: FakeAdapter) -> list[tuple[bool, str]]:
    results = []
    for item in DATA:
        reply = await model.complete([
            Message(role="system", content=JUDGE_PROMPT),
            Message(role="user", content=f"Q: {item.question}\nA: {item.output}"),
        ])
        verdict = json.loads(reply.content)
        results.append((bool(verdict["pass"]), verdict["critique"]))
    return results


# %% agreement_and_kappa
def cohen_kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    agree = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    expected = pa * pb + (1 - pa) * (1 - pb)  # agreement expected by chance
    return 0.0 if expected == 1 else (agree - expected) / (1 - expected)


async def main() -> None:
    judged = await judge_all(scripted_judge())
    human = [d.human_pass for d in DATA]
    model = [p for p, _ in judged]
    agree = sum(h == m for h, m in zip(human, model)) / len(DATA)
    print(f"agreement {agree:.0%}  kappa {cohen_kappa(human, model):.2f}  (judge {'LENIENT' if INJECT_LENIENT_JUDGE else 'calibrated'})")
    tp = sum(h and m for h, m in zip(human, model)); fn = sum(h and not m for h, m in zip(human, model))
    fp = sum((not h) and m for h, m in zip(human, model)); tn = sum((not h) and (not m) for h, m in zip(human, model))
    print(f"  human pass / judge pass: {tp}   human pass / judge fail: {fn}")
    print(f"  human fail / judge pass: {fp}   human fail / judge fail: {tn}")
    print("disagreements (fix the judge prompt with these critiques as few-shot examples):")
    for item, (p, critique) in zip(DATA, judged):
        if p != item.human_pass:
            print(f"  #{item.id}: judge={'pass' if p else 'fail'} human={'pass' if item.human_pass else 'fail'} | human said: {item.human_critique}")


if __name__ == "__main__":
    asyncio.run(main())
