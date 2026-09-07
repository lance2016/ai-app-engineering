"""Check that every `complete` lesson and prerequisite module keeps its promise.

Run:  uv run python scripts/check_lesson_template.py           # errors fail, warnings print
      uv run python scripts/check_lesson_template.py --strict  # warnings also fail

`complete` in a README's frontmatter promises the reader gets what AGENTS.md
3.2 lists. Most of that list is a judgement call and is left to review; this
script checks the three items a string search can find:

  * 怎么测 -- the lesson says how to verify the mechanism it teaches. Looked
    for anywhere in the text, not under a heading, because a lesson names that
    section after its own subject.
  * a link to ai-app-engineering-ref -- where the reference implementation is.
  * 访问日期 -- at least one dated external source.

Lessons written before 2026-09-07 followed a fixed heading template. AGENTS.md
3.7 retired it: new and rewritten lessons set `structure: narrative` in their
frontmatter and are checked only on the three items above. A lesson without
that line is treated as not yet migrated and still has to carry the old
headings (LESSON_SECTIONS), so a small edit cannot silently drop a section.
That list lives here and nowhere else; it is a fence around old lessons, not
a shape for new ones.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LESSON_SECTIONS = ["为什么需要", "学习目标", "怎么理解它", "机制拆解", "常见错误", "取舍", "框架映射", "参考实现", "延伸阅读"]
OPTIONAL_SECTIONS = ["前置", "工程落地", "一线经验"]
# What every complete lesson owes the reader, in the form a string search can
# find. The rest of AGENTS.md 3.2 (what problem, what you learn, how it fails)
# is checked by review, not here.
CONTENT_CHECKS = [
    ("怎么测", "nothing says 怎么测 -- every lesson leaves a sample that can join the golden set (AGENTS.md 3.2)"),
    ("ai-app-engineering-ref", "no link to ai-app-engineering-ref (AGENTS.md 3.2)"),
    ("访问日期", "no external source with 访问日期 (AGENTS.md 3.2)"),
]
# 起步课没有前置，也不谈落地和一线经验，不必每次都提醒。
EXEMPT_FROM_OPTIONAL = {"setup"}
# 第 00 课只跑通一次调用，没有可以留进 golden set 的东西。
EXEMPT_FROM_HOW_TO_TEST = {"setup"}
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
    meta = frontmatter(readme)
    if meta.get("status") != "complete":
        return errors, warnings
    text = readme.read_text(encoding="utf-8")
    found = headings(readme)
    is_lesson = sections is LESSON_SECTIONS
    legacy = is_lesson and meta.get("structure") != "narrative"
    if not is_lesson or legacy:
        for s in sections:
            if s not in found:
                errors.append(f"missing section '## {s}'")
    if legacy and readme.parent.name not in EXEMPT_FROM_OPTIONAL:
        for s in OPTIONAL_SECTIONS:
            if s not in found:
                warnings.append(f"no '## {s}' section")
    if is_lesson:
        for needle, message in CONTENT_CHECKS:
            if needle == "怎么测" and readme.parent.name in EXEMPT_FROM_HOW_TO_TEST:
                continue
            if needle not in text:
                errors.append(message)
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
