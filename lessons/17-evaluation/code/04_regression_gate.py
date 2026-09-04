"""A regression gate: compare this run against a saved baseline and fail on drops.

Overall pass rate hides slice regressions, so the gate checks every slice.
The baseline is a JSON file written by a previous accepted run. Thresholds are
product decisions; here they are constants so the mechanism is visible.

Run:  uv run python lessons/17-evaluation/code/04_regression_gate.py                # v1 vs baseline: pass
      INJECT_REGRESSION=1 uv run python lessons/17-evaluation/code/04_regression_gate.py   # v2 vs baseline: exit 1
Expect: the v2 prompt stays inside the overall tolerance (83% vs 100%) but the
        adversarial slice drops far below tolerance, so the gate refuses it.
"""

# %% imports
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

INJECT_REGRESSION = os.environ.get("INJECT_REGRESSION") == "1"
BASELINE = Path(os.environ.get("CHECKPOINT_DIR", tempfile.gettempdir())) / "aiapp_lesson17_baseline.json"
MAX_OVERALL_DROP = 0.20  # with 12 cases one failure is 8 points; a coarse overall threshold is inevitable
MAX_SLICE_DROP = 0.10  # slices are where regressions actually show


# %% reuse_lesson_evaluator
def load_evaluator():
    """Import 01_golden_set_assertions.py from this directory (module names cannot start with digits)."""
    path = Path(__file__).with_name("01_golden_set_assertions.py")
    spec = importlib.util.spec_from_file_location("golden", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scores(report) -> dict:
    return {"overall": report.rate(), "slices": {tag: ok / n for tag, (ok, n) in report.by_tag.items()}}


# %% gate
def gate(current: dict, baseline: dict) -> list[str]:
    problems = []
    if baseline["overall"] - current["overall"] > MAX_OVERALL_DROP:
        problems.append(f"overall {baseline['overall']:.0%} -> {current['overall']:.0%}")
    for tag, base in baseline["slices"].items():
        now = current["slices"].get(tag, 0.0)
        if base - now > MAX_SLICE_DROP:
            problems.append(f"slice {tag} {base:.0%} -> {now:.0%}")
    return problems


# %% run
def main() -> int:
    golden = load_evaluator()
    if not BASELINE.exists():
        BASELINE.write_text(json.dumps(scores(golden.evaluate("v1")), indent=2), encoding="utf-8")
        print(f"no baseline yet; recorded v1 as baseline at {BASELINE}")
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    version = "v2" if INJECT_REGRESSION else "v1"
    current = scores(golden.evaluate(version))
    print(f"candidate {version}: overall {current['overall']:.0%} (baseline {baseline['overall']:.0%})")
    problems = gate(current, baseline)
    if problems:
        print("GATE FAILED:")
        for p in problems:
            print(f"  {p}")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
