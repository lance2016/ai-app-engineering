"""Check that every `complete` lesson and prerequisite module actually meets the template.

Run:  uv run python scripts/check_lesson_template.py           # errors fail, warnings print
      uv run python scripts/check_lesson_template.py --strict  # warnings also fail

`complete` in a README's frontmatter promises: every template section is
present, `code/` has at least one runnable .py, `exercises.md` exists and has
folded answers. Sections listed in FUTURE_SECTIONS are the template additions
from the 2026-09 restructure; they are warnings until the retrofit is done.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LESSON_SECTIONS = ["学习目标", "前置", "心智模型", "最小可运行例子", "常见错误与失败注入", "取舍", "练习", "对照真实项目", "延伸阅读"]
FUTURE_SECTIONS = ["为什么需要", "生产方案", "框架映射"]
PREREQ_SECTIONS = ["学习目标", "前置", "核心概念", "动手", "常见错误", "练习", "它在 AI 应用里用在哪", "延伸阅读"]
MILESTONE_SECTIONS = ["这一步加什么", "验收证据", "依赖的课程"]


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    return dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))


def headings(path: Path) -> set[str]:
    return {h.strip() for h in re.findall(r"^## (.+)$", path.read_text(encoding="utf-8"), re.M)}


def check_unit(readme: Path, sections: list[str], *, needs_code: bool, needs_exercises: bool) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    fm = frontmatter(readme)
    if fm.get("status") != "complete":
        return errors, warnings
    found = headings(readme)
    for s in sections:
        if s not in found:
            errors.append(f"missing section '## {s}'")
    for s in FUTURE_SECTIONS if sections is LESSON_SECTIONS else []:
        if s not in found:
            warnings.append(f"missing new-template section '## {s}'")
    unit = readme.parent
    if needs_code:
        code = list((unit / "code").glob("*.py"))
        if not code:
            errors.append("code/ has no .py file")
        elif sections is LESSON_SECTIONS and not any("INJECT_" in p.read_text(encoding="utf-8") for p in code):
            warnings.append("no INJECT_ switch in code/ (failure injection should be reproducible)")
    if needs_exercises:
        ex = unit / "exercises.md"
        if not ex.exists():
            errors.append("exercises.md missing")
        elif "<details>" not in ex.read_text(encoding="utf-8"):
            errors.append("exercises.md has no folded <details> answers")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args()

    units = [
        *((p, LESSON_SECTIONS, True, True) for p in sorted(ROOT.glob("lessons/*/README.md"))),
        *((p, PREREQ_SECTIONS, True, True) for p in sorted(ROOT.glob("prerequisites/*/*/README.md"))),
        *((p, MILESTONE_SECTIONS, False, False) for p in sorted(ROOT.glob("project/m*/README.md"))),
    ]
    total_errors = total_warnings = 0
    for readme, sections, needs_code, needs_exercises in units:
        errors, warnings = check_unit(readme, sections, needs_code=needs_code, needs_exercises=needs_exercises)
        rel = readme.relative_to(ROOT)
        for e in errors:
            print(f"ERROR {rel}: {e}")
        for w in warnings:
            print(f"WARN  {rel}: {w}")
        total_errors += len(errors)
        total_warnings += len(warnings)
    print(f"{len(units)} units checked, {total_errors} error(s), {total_warnings} warning(s)")
    if total_errors or (args.strict and total_warnings):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
