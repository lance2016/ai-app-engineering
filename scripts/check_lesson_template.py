"""Check that every `complete` lesson and prerequisite module meets the template.

Run:  uv run python scripts/check_lesson_template.py           # errors fail, warnings print
      uv run python scripts/check_lesson_template.py --strict  # warnings also fail

`complete` in a README's frontmatter promises that every required section is
present. Sections in OPTIONAL_SECTIONS are recommended but not every topic
has them.

Every `complete` lesson must also say how to test the thing it teaches. That
rule predates this script (AGENTS.md 3.0 makes "怎么测" the last item under
工程落地) and was silently unmet by thirteen lessons, so it is checked here
now rather than trusted. The check looks for the phrase anywhere in the
lesson, not under a fixed heading, because a narrative lesson names that
section after its own subject.

A lesson may set `structure: narrative` in its frontmatter to opt out of the
fixed heading list and organise its own narrative. Then only CONTRACT_SECTIONS
are required: the headings whose names are functional labels a reader looks
things up by, rather than framing the author should be choosing per topic.
Twenty-six lessons that all open with `## 为什么需要` and close with
`## 延伸阅读` read as one article with the nouns swapped, which is what this
escape hatch exists to fix. It is an opt-in, so a lesson that says nothing
still gets the full check.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LESSON_SECTIONS = ["为什么需要", "学习目标", "怎么理解它", "机制拆解", "常见错误", "取舍", "框架映射", "参考实现", "延伸阅读"]
OPTIONAL_SECTIONS = ["前置", "工程落地", "一线经验"]
# What a `structure: narrative` lesson still owes the reader. The five that
# stay are the ones people navigate by ("what breaks", "what is this called in
# LangGraph"); the six that drop out are framing -- 为什么需要, 怎么理解它,
# 机制拆解, 取舍, 工程落地, 一线经验 -- and each topic should be naming those
# after the thing it is actually about.
CONTRACT_SECTIONS = ["学习目标", "常见错误", "框架映射", "参考实现", "延伸阅读"]
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
    found = headings(readme)
    is_lesson = sections is LESSON_SECTIONS
    narrative = is_lesson and meta.get("structure") == "narrative"
    if narrative:
        sections = CONTRACT_SECTIONS
    for s in sections:
        if s not in found:
            errors.append(f"missing section '## {s}'")
    if sections is LESSON_SECTIONS and readme.parent.name not in EXEMPT_FROM_OPTIONAL:
        for s in OPTIONAL_SECTIONS:
            if s not in found:
                warnings.append(f"no '## {s}' section")
    if is_lesson and readme.parent.name not in EXEMPT_FROM_HOW_TO_TEST:
        if "怎么测" not in readme.read_text(encoding="utf-8"):
            errors.append("nothing says 怎么测 -- every lesson leaves a sample "
                          "that can join the golden set (AGENTS.md 3.0)")
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
