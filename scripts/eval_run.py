"""Run every evaluation suite, calibrate the judge, compare with the baseline, write a report. Exit 1 when the gate fails.

Run:  uv run python scripts/eval_run.py                                  # gate against project/eval/baseline.json
      uv run python scripts/eval_run.py --update-baseline               # accept the current numbers as the new baseline
      uv run python scripts/eval_run.py --report project/eval/reports/$(date +%F).md
      MODEL_PROVIDER=deepseek uv run python scripts/eval_run.py --real-tools   # tool-selection suite against a real model
      INJECT_REGRESSION=1 uv run python scripts/eval_run.py              # rehearse a failing gate (tools slice collapses)
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, get_adapter
from aiapp.eval.gate import Thresholds, gate, load_baseline, scores
from aiapp.eval.judge import calibrate, scripted_judge
from aiapp.eval.suites import load_jsonl, run_retrieval, run_tasks, run_tools
from aiapp.ops import telemetry

ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "project/eval"
BASELINE = EVAL_DIR / "baseline.json"
THRESHOLDS = EVAL_DIR / "thresholds.toml"


async def run(real_tools: bool) -> tuple[list, object]:
    tools_model = None
    if os.environ.get("INJECT_REGRESSION") == "1":  # a model that never picks a tool: the "search" slice collapses
        tools_model = FakeAdapter(script=[ModelResponse(content="Sure.")] * 50)
    elif real_tools:
        tools_model = get_adapter(os.environ.get("MODEL_PROVIDER"))
    suites = [await run_tasks(), await run_tools(tools_model), await run_retrieval()]
    judge_cases = load_jsonl(EVAL_DIR / "judge_calibration.jsonl")
    judge = get_adapter(os.environ["MODEL_PROVIDER"]) if os.environ.get("MODEL_PROVIDER", "fake") != "fake" and os.environ.get("REAL_JUDGE") == "1" else scripted_judge(judge_cases)
    calibration = await calibrate(judge_cases, judge)
    return suites, calibration


def render(suites, calibration, current, baseline, report, thresholds) -> str:
    lines = [f"# Eval report {datetime.now(UTC).isoformat(timespec='seconds')}", "", f"Gate: **{'PASS' if report.passed else 'FAIL'}**", ""]
    lines += ["| suite | n | pass rate | baseline | floor |", "|---|---|---|---|---|"]
    for s in suites:
        base = baseline.get(s.name, {}).get("overall") if baseline else None
        lines.append(f"| {s.name} | {len(s.results)} | {s.pass_rate:.0%} | {f'{base:.0%}' if base is not None else '-'} | {thresholds.floors.get(s.name, 0):.0%} |")
    lines += ["", "## Slices", ""]
    for s in suites:
        for tag, rate in s.slices().items():
            lines.append(f"- {s.name} / {tag}: {rate:.0%}")
    lines += ["", f"## Judge calibration (n={calibration.n})", "", f"agreement {calibration.agreement:.0%}, Cohen's kappa {calibration.kappa:.2f} (min {thresholds.judge_min_kappa:.2f})"]
    for d in calibration.disagreements:
        lines.append(f"- {d['id']}: judge={'pass' if d['judge'] else 'fail'} human={'pass' if d['human'] else 'fail'}; human said: {d['human_critique']}")
    failures = [(s.name, f) for s in suites for f in s.failures()]
    if failures:
        lines += ["", "## Failures", ""] + [f"- {name}/{f.case_id}: {f.reason}" for name, f in failures]
    if report.problems or report.warnings:
        lines += ["", "## Gate"] + [f"- PROBLEM: {p}" for p in report.problems] + [f"- warning: {w}" for w in report.warnings]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--real-tools", action="store_true", help="run the tool-selection suite against MODEL_PROVIDER")
    args = parser.parse_args()

    telemetry.setup_tracing(in_memory=True)  # the runtime emits spans; keep them local during evaluation
    suites, calibration = asyncio.run(run(args.real_tools))
    thresholds = Thresholds.load(THRESHOLDS)
    current = scores(suites)
    baseline = load_baseline(BASELINE)
    report = gate(current, baseline, thresholds, judge_kappa=calibration.kappa)
    text = render(suites, calibration, current, baseline, report, thresholds)
    print(text)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    if args.update_baseline:
        BASELINE.write_text(json.dumps({"recorded_at": datetime.now(UTC).isoformat(timespec="seconds"), **current}, indent=2), encoding="utf-8")
        print(f"baseline written to {BASELINE}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
