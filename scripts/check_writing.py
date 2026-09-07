"""Count the sentence patterns AGENTS.md 4.1 and 4.3 ask writers to ration.

Run:  uv run python scripts/check_writing.py            # report + fail over ceiling
      uv run python scripts/check_writing.py --report    # print the numbers, never fail

Why a script. The rules in AGENTS.md 4.1 were written after an antislop audit
(anti-slop/audit-001-2026-09-07.md) found the same handful of shapes repeated
across all 26 lessons, and for a year nothing measured them, so they drifted.
Some of the rules are judgement calls a script has no business making -- "is X
a misconception the reader actually holds" is one -- so this does not try to
be a linter. It counts, and it fails when a count goes UP.

The ceilings are a ratchet, not a target. They sit at wherever the number was
when this file was last touched, so ordinary editing cannot raise them by
accident. Lowering one is the normal thing to do: fix some prose, then bring
the number down in the same commit. Raising one needs a reason in the commit
message, and adding a lesson is a reason.

Two of the counts are zero and stay zero, because the shapes have no
legitimate use: announcing a list's length before writing it, and closing a
tradeoff bullet with a bolded epigram.
"""

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = sorted(ROOT.glob("lessons/*/README.md"))
# The counts that span the whole course also look at the prose outside lessons.
WIDE = LESSONS + [
    *sorted(ROOT.glob("prerequisites/**/README.md")),
    *sorted(ROOT.glob("principles/*.md")),
    *sorted(ROOT.glob("reference/*.md")),
    ROOT / "docs/index.md",
]

# The tradeoff section is named after its subject in `structure: narrative`
# lessons, so it is matched by what it does rather than by one heading.
TRADEOFF_HEADINGS = ("取舍", "松一点", "记多少", "接一个 server",
                     "上限设多少", "透明到什么程度")

BOLD = re.compile(r"\*\*([^*\n]+)\*\*")
LEADS_WITH_BOLD = re.compile(r"^\s*(?:-|\d+\.)?\s*\*\*")
COUNT_LEAD = re.compile(r"^(?:另外)?[两三四五六]个要点[:：]\s*$", re.M)
NEGATION = re.compile(r"不是[^。，；]{1,24}(?:，是|，而是)|而不是")
BOLD_CLOSER = re.compile(r"\*\*[^*]{4,40}\*\*\s*$")

# Bold spans that are a document's own field labels rather than emphasis.
# `二、ADR：多两个字段` shows an example ADR whose fields are bolded the way
# any template's fields are.
EMPHASIS_EXEMPT = {("system-design-decisions", "机制拆解", "二、ADR：多两个字段")}

CEILINGS = {
    "negation": 93,         # 「不是 X，是 Y」and「而不是」across the course
    "zhenzheng": 29,        # 「真正」
    "count_lead": 0,        # 「三个要点：」and friends -- no legitimate use
    "bold_closer": 0,       # a tradeoff bullet ending on a bolded epigram
    "dense_emphasis": 0,    # subsections over three prose emphases
}


def slug(path: Path) -> str:
    return path.parent.name


def strip_fences(text: str) -> str:
    return "".join(text.split("```")[::2])


def emphasis_per_subsection(path: Path) -> Counter:
    """Bold spans that are emphasis, keyed by the smallest enclosing heading.

    A bold that starts a line is that item's or paragraph's label, which is the
    convention 常见错误 and 工程落地 are written in; only the rest is emphasis.
    Table cells are skipped: a bold there marks the one row that is the odd one.
    """
    counts: Counter = Counter()
    h2 = h3 = None
    for line in strip_fences(path.read_text(encoding="utf-8")).splitlines():
        if line.startswith("## "):
            h2, h3 = line[3:].strip(), None
            continue
        if line.startswith("### "):
            h3 = line[4:].strip()
            continue
        if not h2 or line.startswith("| "):
            continue
        found = BOLD.findall(line)
        if not found:
            continue
        if LEADS_WITH_BOLD.match(line):
            found = found[1:]
        counts[(slug(path), h2, h3 or "—")] += len(found)
    return counts


def tradeoff_bullets(path: Path) -> list[str]:
    out, on = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            on = any(k in line for k in TRADEOFF_HEADINGS)
            continue
        if on and line.startswith("- **"):
            out.append(line)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", action="store_true",
                        help="print the counts without failing")
    args = parser.parse_args()

    counts, detail = {}, {}

    wide = "\n".join(strip_fences(p.read_text(encoding="utf-8")) for p in WIDE)
    counts["negation"] = len(NEGATION.findall(wide))
    counts["zhenzheng"] = wide.count("真正")

    leads = [(slug(p), m) for p in LESSONS
             for m in COUNT_LEAD.findall(p.read_text(encoding="utf-8"))]
    counts["count_lead"] = len(leads)
    detail["count_lead"] = [f"{s}: {m.strip()}" for s, m in leads]

    closers = [(slug(p), b) for p in LESSONS for b in tradeoff_bullets(p)
               if BOLD_CLOSER.search(b.rstrip())]
    counts["bold_closer"] = len(closers)
    detail["bold_closer"] = [f"{s}: {b[:60]}" for s, b in closers]

    dense = [(k, v) for p in LESSONS
             for k, v in emphasis_per_subsection(p).items()
             if v > 3 and k not in EMPHASIS_EXEMPT]
    counts["dense_emphasis"] = len(dense)
    detail["dense_emphasis"] = [
        f"{v} emphases in {k[0]} / {k[1]}" + (f" / {k[2]}" if k[2] != "—" else "")
        for k, v in dense]

    bad = 0
    for key, ceiling in CEILINGS.items():
        got = counts[key]
        over = got > ceiling
        bad += over
        mark = "OVER " if over else "ok   "
        print(f"{mark}{key:16s} {got:4d}  (ceiling {ceiling})")
        for line in detail.get(key, []) if over else []:
            print(f"      {line}")

    total_bold = sum(len(BOLD.findall(strip_fences(p.read_text(encoding="utf-8"))))
                     for p in LESSONS)
    print(f"\n{total_bold} bold spans across {len(LESSONS)} lessons "
          f"({total_bold / len(LESSONS):.0f} per lesson). Not a gate; "
          f"dense_emphasis is the one that bites.")

    if bad and not args.report:
        print("\nA count went up. Either fix the prose, or lower the ceiling in "
              "this file in the same commit and say why.")
    return 1 if bad and not args.report else 0


if __name__ == "__main__":
    sys.exit(main())
