"""Check that every `complete` lesson and prerequisite module meets the template.

Run:  uv run python scripts/check_lesson_template.py           # errors fail, warnings print
      uv run python scripts/check_lesson_template.py --strict  # warnings also fail

`complete` in a README's frontmatter promises that every required section is
present. Sections in OPTIONAL_SECTIONS are recommended but not every topic
has them.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LESSON_SECTIONS = ["为什么需要", "学习目标", "怎么理解它", "机制拆解", "常见错误", "取舍", "框架映射", "参考实现", "延伸阅读"]
OPTIONAL_SECTIONS = ["前置", "工程落地", "一线经验"]
# 起步课没有前置，也不谈落地和一线经验，不必每次都提醒。
EXEMPT_FROM_OPTIONAL = {"setup"}
PREREQ_SECTIONS = ["学习目标", "核心概念", "常见错误", "延伸阅读"]


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    return dict(re.findall(r"^(\w+):\s*(.+)$", m.group(1), re.M))


def headings(path: Path) -> set[str]:
    return {h.strip() for h in re.findall(r"^## (.+)$", path.read_text(encoding="utf-8"), re.M)}


def check_unit(readme: Path, sections: list[str]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if frontmatter(readme).get("status") != "complete":
        return errors, warnings
    found = headings(readme)
    for s in sections:
        if s not in found:
            errors.append(f"missing section '## {s}'")
    if sections is LESSON_SECTIONS and readme.parent.name not in EXEMPT_FROM_OPTIONAL:
        for s in OPTIONAL_SECTIONS:
            if s not in found:
                warnings.append(f"no '## {s}' section")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = parser.parse_args()

    units = [
        *((p, LESSON_SECTIONS) for p in sorted(ROOT.glob("lessons/*/README.md"))),
        *((p, PREREQ_SECTIONS) for p in sorted(ROOT.glob("prerequisites/*/*/README.md"))),
    ]
    total_errors = total_warnings = 0
    for readme, sections in units:
        errors, warnings = check_unit(readme, sections)
        rel = readme.relative_to(ROOT)
        for e in errors:
            print(f"ERROR {rel}: {e}")
        for w in warnings:
            print(f"WARN  {rel}: {w}")
        total_errors += len(errors)
        total_warnings += len(warnings)
    print(f"{len(units)} units checked, {total_errors} error(s), {total_warnings} warning(s)")
    return 1 if total_errors or (args.strict and total_warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
