"""Fail if a lesson number written as prose names a lesson that does not exist,
or contradicts the nav.

Run:  uv run python scripts/check_lesson_refs.py

check_links.py already validates the numbers that carry a link, as in
`[15 RAG 端到端](../rag-end-to-end/README.md)`. It cannot see the other kind:
「第 08 课整课都在讲这个列表怎么裁」, a `07 · 08 · 15` cell in a table on the
overview, a number in a front-page blurb. Those carry no path, so inserting a
lesson leaves every one of them pointing at whichever lesson now sits at that
number, and both existing checks stay green.

Three checks, all sourced from the nav in mkdocs.yml:

  * 第 NN 课 -- NN must be a lesson that exists. 「第 31 课」 in a 27-lesson
    course is a typo or a leftover from an older numbering.
  * 第 NN 课 <title> -- when a title follows the number, it has to be that
    lesson's title. 「第 19 课 RAG 端到端」 is caught, because 15 is the RAG
    lesson.
  * a table cell that is a list of lesson numbers (`| 07 · 08 · 15 |`) --
    every number in it must exist.
  * `[第 15 课 Memory](../lessons/memory/README.md)` -- the number must match
    the lesson it links to. check_links.py wants a digit right after the
    bracket, so this shape (common in prerequisites/) slips past it.

Exit code 1 on any of them. Numbers inside fenced code blocks are skipped.
"""

import re
import sys
from pathlib import Path

from check_links import iter_markdown, strip_code_blocks
from sync_numbering import MKDOCS, order

ROOT = Path(__file__).resolve().parents[1]

# `- 05 Tool Calling: lessons/tool-calling/README.md` in the nav block.
NAV_LABEL_RE = re.compile(r"-\s*(\d{2})\s+([^:\n]+?)\s*:\s*lessons/([a-z0-9-]+)/README\.md")
BARE_RE = re.compile(r"第 ?(\d{1,2}) ?课")
# The number, then optionally a title right after it. Only a title that sits
# immediately after the number is checked -- 「第 11 课讲 MCP 和 handoff」 names
# no title, and reading the whole sentence would flag it.
TITLED_RE = re.compile(r"第 ?(\d{1,2}) ?课[的\s：:]{0,2}([A-Za-z一-龥][^，。；、）】()\[\]\n]{0,16})")
# A cell that is a list of lesson numbers: `| 07 · 08 · 15 |`. A cell with a
# single number is skipped -- `| 32 |` in a trace table is a step count, and
# nothing in the text distinguishes the two.
NUM_CELL_RE = re.compile(r"\|\s*(\d{2}(?:\s*[·,、]\s*\d{2})+)\s*(?=\|)")
# `[第 15 课 Memory](../../lessons/memory/README.md)` -- check_links.py's
# pattern wants a digit right after the bracket, so this shape slips past it.
LINKED_RE = re.compile(r"\[第 ?(\d{1,2}) 课[^\]]*\]\([^)]*?([a-z0-9-]+)/README\.md\)")


def nav_titles() -> dict[str, str]:
    """Lesson number -> title, from the nav labels."""
    text = MKDOCS.read_text(encoding="utf-8")
    return {num: title for num, title, _ in NAV_LABEL_RE.findall(text)}


def check(md: Path, total: int, titles: dict[str, str], number_of: dict[str, str]) -> list[str]:
    text = strip_code_blocks(md.read_text(encoding="utf-8"))
    problems = []

    for num, slug in LINKED_RE.findall(text):
        want = number_of.get(slug)      # not a lesson (a prerequisite, say)
        if want and f"{int(num):02d}" != want:
            problems.append(f"[第 {num} 课 ...] points at {slug}, which is {want}")

    for num in BARE_RE.findall(text):
        if not 0 <= int(num) < total:
            problems.append(f"第 {num} 课 does not exist ({total} lessons: 00-{total - 1:02d})")

    for num, tail in TITLED_RE.findall(text):
        key = f"{int(num):02d}"
        for other, title in titles.items():
            if other == key:
                continue
            # Written as the full title, or the head of it (「RAG」 for
            # 「RAG 端到端」). Three characters minimum, so that a stray word
            # does not collide with a short title.
            head = tail[: len(title)]
            if len(head) >= 3 and (head == title or title.startswith(head)):
                problems.append(
                    f"第 {num} 课 {tail!r} -- that title belongs to {other} "
                    f"({titles.get(key, '?')} is {key})"
                )
                break

    for cell in NUM_CELL_RE.findall(text):
        for num in re.findall(r"\d{2}", cell):
            if int(num) >= total:
                problems.append(f"table cell `{cell}` names 第 {num} 课, which does not exist")
    return problems


def main() -> int:
    seq = order()
    titles = nav_titles()
    number_of = {slug: f"{i:02d}" for i, slug in enumerate(seq)}
    if len(titles) != len(seq):
        print(f"WARN  nav has {len(seq)} lessons but {len(titles)} parsable labels")
    bad = 0
    files = iter_markdown()
    for md in files:
        rel = md.relative_to(ROOT)
        for note in check(md, len(seq), titles, number_of):
            print(f"ERROR {rel}: {note}")
            bad += 1
    print(f"{len(files)} files checked, {bad} stale lesson reference(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
