"""The evaluation suites pass on the shipped runtime, the gate catches a regression, and the judge calibration math holds."""

import asyncio
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse
from aiapp.eval.gate import Thresholds, gate, scores
from aiapp.eval.judge import calibrate, cohen_kappa, scripted_judge
from aiapp.eval.suites import load_jsonl, run_retrieval, run_tasks, run_tools

ROOT = Path(__file__).resolve().parents[3]
THRESHOLDS = Thresholds.load(ROOT / "project/eval/thresholds.toml")


def test_task_suite_passes_on_the_current_runtime() -> None:
    suite = asyncio.run(run_tasks())
    assert suite.pass_rate == 1.0, [f"{f.case_id}: {f.reason}" for f in suite.failures()]
    assert {"safety", "side_effect", "robustness", "hitl", "skills"} <= set(suite.slices())


def test_tools_and_retrieval_suites_meet_their_floors() -> None:
    tools, retrieval = asyncio.run(run_tools()), asyncio.run(run_retrieval())
    assert tools.pass_rate >= THRESHOLDS.floors["tools"] and retrieval.pass_rate >= THRESHOLDS.floors["retrieval"]


def test_gate_catches_an_overall_and_a_slice_regression() -> None:
    baseline = {"tools": {"overall": 1.0, "slices": {"search": 1.0, "chat": 1.0}, "n": 20}}
    fine = {"tools": {"overall": 0.97, "slices": {"search": 0.95, "chat": 1.0}, "n": 20}}
    assert gate(fine, baseline, THRESHOLDS).passed
    slice_drop = {"tools": {"overall": 0.96, "slices": {"search": 1.0, "chat": 0.6}, "n": 20}}
    report = gate(slice_drop, baseline, THRESHOLDS)
    assert not report.passed and any("slice chat" in p for p in report.problems), "the overall rate hides it; the slice does not"
    collapse = asyncio.run(run_tools(FakeAdapter(script=[ModelResponse(content="Sure.")] * 50)))
    report = gate(scores([collapse]), baseline, THRESHOLDS)
    assert not report.passed and any("below the floor" in p for p in report.problems)


def test_judge_calibration_reports_agreement_and_kappa() -> None:
    cases = load_jsonl(ROOT / "project/eval/judge_calibration.jsonl")
    cal = asyncio.run(calibrate(cases, scripted_judge(cases)))
    assert cal.n == 20 and 0.8 <= cal.agreement < 1.0 and cal.kappa > THRESHOLDS.judge_min_kappa
    assert {d["id"] for d in cal.disagreements} == {"j04", "j12", "j18"}, "the judge is lenient on vague or over-claiming answers; those critiques become few-shot examples"
    lenient = FakeAdapter(script=[ModelResponse(content='{"pass": true, "critique": "fine"}')] * 20)
    lenient_cal = asyncio.run(calibrate(cases, lenient))
    assert lenient_cal.kappa == 0.0 and abs(lenient_cal.agreement - 0.55) < 1e-9, "a judge that passes everything agrees on every human pass (11/20) and is still worthless: kappa 0"
    assert cohen_kappa([True, False, True, False], [True, False, True, False]) == 1.0
