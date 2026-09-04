"""The regression gate: every suite and every slice must stay within tolerance of the baseline, and above the floor."""

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from aiapp.eval.suites import SuiteResult


@dataclass
class Thresholds:
    floors: dict[str, float]  # suite -> minimum pass rate regardless of baseline
    max_drop: float  # allowed drop vs baseline, overall
    max_slice_drop: float
    judge_min_kappa: float

    @classmethod
    def load(cls, path: Path) -> "Thresholds":
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        return cls(floors=raw["floors"], max_drop=raw["gate"]["max_drop"], max_slice_drop=raw["gate"]["max_slice_drop"], judge_min_kappa=raw["judge"]["min_kappa"])


@dataclass
class GateReport:
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


def scores(suites: list[SuiteResult]) -> dict:
    return {s.name: {"overall": round(s.pass_rate, 4), "slices": {k: round(v, 4) for k, v in s.slices().items()}, "n": len(s.results)} for s in suites}


def gate(current: dict, baseline: dict | None, thresholds: Thresholds, *, judge_kappa: float | None = None) -> GateReport:
    report = GateReport()
    for name, cur in current.items():
        floor = thresholds.floors.get(name)
        if floor is not None and cur["overall"] < floor:
            report.problems.append(f"{name}: {cur['overall']:.0%} is below the floor {floor:.0%}")
        if baseline and name in baseline:
            base = baseline[name]
            if base["overall"] - cur["overall"] > thresholds.max_drop:
                report.problems.append(f"{name}: overall {base['overall']:.0%} -> {cur['overall']:.0%}")
            for tag, base_rate in base["slices"].items():
                now = cur["slices"].get(tag, 0.0)
                if base_rate - now > thresholds.max_slice_drop:
                    report.problems.append(f"{name}: slice {tag} {base_rate:.0%} -> {now:.0%}")
    if judge_kappa is not None and judge_kappa < thresholds.judge_min_kappa:
        report.warnings.append(f"judge kappa {judge_kappa:.2f} below {thresholds.judge_min_kappa:.2f}: do not trust the judge on open-ended answers yet")
    return report


def load_baseline(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
