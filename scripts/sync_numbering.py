"""Lesson numbers come from the nav in mkdocs.yml, not from directory names.

Run:  uv run python scripts/sync_numbering.py           # fix the numbers in place
      uv run python scripts/sync_numbering.py --check   # report only, for CI

Lesson directories carry no number (`lessons/tool-calling/`), so a URL, a
bookmark and a reader's saved progress all survive a lesson being inserted in
the middle. The order lives in exactly one place -- the `主线课程` section of
mkdocs.yml -- and this script pushes the numbers it implies out to the three
places a reader actually sees one:

  1. the contents on the front page   -- <span>NN</span> and data-lesson
  2. the footer of every lesson       -- 上一课 / 下一课
  3. the per-Part tables in lessons/README.md
  4. each lesson's h1
  5. the nav labels in mkdocs.yml itself

So inserting a lesson is: create the directory, add one nav line, run this.
Nothing else renumbers, because nothing else stores a number.

It also fails when the three sets of lessons disagree -- nav, the directories
on disk, and the front page -- which is the mistake that actually breaks the
site: a lesson that exists but is unreachable, or is listed but not written.

Prose that counts the lessons ("26 课", "26 格尺规") is reported, never
rewritten: "27 课" may be the right edit, or the sentence may want rewording,
and that is a judgement call.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MKDOCS = ROOT / "mkdocs.yml"
INDEX = ROOT / "docs/index.md"
OVERVIEW = ROOT / "lessons/README.md"
# Prose that states how many lessons there are ("26 课", "26 格尺规").
COUNTED = ["docs/index.md", "README.md", "AGENTS.md", "lessons/README.md"]
# `第 18 课` and `第 18、19 课` name lessons rather than count them, so they are
# struck out before the count is looked for.
NAMES_RE = re.compile(r"第 ?\d+(?:\s*[、,，和]\s*\d+)* ?课")
COUNT_RE = re.compile(r"(?<!\d)(\d+) ?[课格]")

# nav entries look like `- 05 Tool Calling: lessons/tool-calling/README.md`.
# `lessons/README.md` is the overview and has no slug segment, so it is skipped.
NAV_RE = re.compile(r"lessons/([a-z0-9-]+)/README\.md")
# Only the nav block. The redirect_maps under `plugins:` name lesson paths too,
# and reading those as course order silently doubles it.
NAV_BLOCK_RE = re.compile(r"^nav:\n(.*?)(?=^\S|\Z)", re.M | re.S)
# The last lesson closes with an extra link out of the course; keep it.
FOOT_RE = re.compile(r"^\[(?:←|.*?下一课).*$", re.M)


def order() -> list[str]:
    """Lesson slugs, in nav order."""
    block = NAV_BLOCK_RE.search(MKDOCS.read_text(encoding="utf-8"))
    if not block:
        raise SystemExit("mkdocs.yml has no nav block")
    return NAV_RE.findall(block.group(1))


def on_disk() -> set[str]:
    return {d.name for d in (ROOT / "lessons").iterdir() if d.is_dir()}


def title(slug: str) -> str:
    """The lesson's h1, minus the number the h1 no longer carries."""
    for line in (ROOT / "lessons" / slug / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return re.sub(r"^\d{2}\s+", "", line[2:].strip())
    raise SystemExit(f"{slug}: no h1")


def sync_front_page(num: dict[str, str]) -> list[str]:
    """Front page: the displayed number, and the slug the progress script keys on."""
    text = INDEX.read_text(encoding="utf-8")
    listed, notes = [], []

    def fix(m: re.Match) -> str:
        shown, label, slug, key = m.group(1), m.group(2), m.group(3), m.group(4)
        listed.append(slug)
        if slug not in num:
            notes.append(f"!front page lists {slug}, which the nav does not")
            return m.group(0)
        want = num[slug]
        if shown != want:
            notes.append(f"front page: {slug} shown as {shown}, nav says {want}")
        if key != slug:
            notes.append(f"front page: {slug} keyed as {key}, which progress.js cannot match")
        return f'[<span>{want}</span>{label}](lessons/{slug}/README.md){{ .lsn data-lesson="{slug}" }}'

    out = re.sub(
        r'\[<span>([^<]*)</span>([^\]]*)\]\(lessons/([a-z0-9-]+)/README\.md\)\{ \.lsn data-lesson="([^"]*)" \}',
        fix, text)

    missing = [s for s in num if s not in listed]
    notes += [f"!front page is missing {s}, add it under the right Part" for s in missing]
    if out != text and not ARGS.check:
        INDEX.write_text(out, encoding="utf-8")
    return notes


def sync_overview(num: dict[str, str]) -> list[str]:
    """The per-Part tables on the lessons overview."""
    text = OVERVIEW.read_text(encoding="utf-8")
    notes = []

    def fix(m: re.Match) -> str:
        shown, slug = m.group(1), m.group(2)
        if slug not in num:
            notes.append(f"!overview links {slug}, which the nav does not")
            return m.group(0)
        if shown != num[slug]:
            notes.append(f"overview: {slug} labelled {shown}, nav says {num[slug]}")
        return f"| [{num[slug]}](./{slug}/README.md) |"

    out = re.sub(r"\| \[([^\]]*)\]\(\./([a-z0-9-]+)/README\.md\) \|", fix, text)
    if out != text and not ARGS.check:
        OVERVIEW.write_text(out, encoding="utf-8")
    return notes


def sync_footers(seq: list[str], num: dict[str, str]) -> list[str]:
    """Every lesson's 上一课 / 下一课 line, rebuilt from the nav order."""
    notes = []
    for i, slug in enumerate(seq):
        path = ROOT / "lessons" / slug / "README.md"
        text = path.read_text(encoding="utf-8")
        m = FOOT_RE.search(text)
        if not m:
            notes.append(f"!{slug}: no 上一课/下一课 line")
            continue

        parts = []
        if i:
            prev = seq[i - 1]
            parts.append(f"[← 上一课 {num[prev]}](../{prev}/README.md)")
        if i + 1 < len(seq):
            nxt = seq[i + 1]
            parts.append(f"[下一课 {num[nxt]} →](../{nxt}/README.md)")
        # Whatever the last lesson closes with is written by hand, not here.
        tail = [p for p in m.group(0).split(" · ") if "上一课" not in p and "下一课" not in p]
        line = " · ".join(parts + tail)

        if line != m.group(0):
            notes.append(f"{slug}: footer was {m.group(0)[:40]}...")
            if not ARGS.check:
                path.write_text(text[:m.start()] + line + text[m.end():], encoding="utf-8")
    return notes


def sync_h1(num: dict[str, str]) -> list[str]:
    """Each lesson's own heading, so a shared link still says which lesson it is."""
    notes = []
    for slug, want in num.items():
        path = ROOT / "lessons" / slug / "README.md"
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^# (?:(\d{2})\s+)?(.+)$", text, re.M)
        if not m:
            notes.append(f"!{slug}: no h1")
            continue
        if m.group(1) == want:
            continue
        notes.append(f"{slug}: h1 numbered {m.group(1)}, nav says {want}")
        if not ARGS.check:
            line = f"# {want} {m.group(2)}"
            path.write_text(text[:m.start()] + line + text[m.end():], encoding="utf-8")
    return notes


def sync_nav(num: dict[str, str]) -> list[str]:
    """The sidebar labels. The nav is the source of order, not of numbers."""
    text = MKDOCS.read_text(encoding="utf-8")
    notes = []

    def fix(m: re.Match) -> str:
        indent, shown, label, slug = m.groups()
        want = num[slug]
        if shown != want:
            notes.append(f"nav: {slug} labelled {shown}, position says {want}")
        return f"{indent}- {want} {label}: lessons/{slug}/README.md"

    out = re.sub(r"^( *)- (?:(\d{2}) )?([^:\n]+): lessons/([a-z0-9-]+)/README\.md$",
                 fix, text, flags=re.M)
    if out != text and not ARGS.check:
        MKDOCS.write_text(out, encoding="utf-8")
    return notes


def check_counts(n: int) -> list[str]:
    """Sentences that say how many lessons there are, when they no longer do."""
    notes = []
    for rel in COUNTED:
        for line_no, line in enumerate((ROOT / rel).read_text(encoding="utf-8").splitlines(), 1):
            for said in COUNT_RE.findall(NAMES_RE.sub("", line)):
                if said != str(n):
                    notes.append(f"!{rel}:{line_no} says {said}, there are {n} lessons")
    return notes


def main() -> int:
    seq = order()
    if not seq:
        raise SystemExit("no lessons found in the mkdocs.yml nav")
    if len(seq) != len(set(seq)):
        raise SystemExit("a lesson appears twice in the nav")

    disk = on_disk()
    problems = [f"!nav lists {s}, no such directory" for s in seq if s not in disk]
    problems += [f"!lessons/{s}/ exists but is not in the nav" for s in sorted(disk - set(seq))]

    num = {slug: f"{i:02d}" for i, slug in enumerate(seq)}
    problems += sync_front_page(num)
    problems += sync_overview(num)
    problems += sync_footers(seq, num)
    problems += sync_h1(num)
    problems += sync_nav(num)
    problems += check_counts(len(seq))

    auto = [p for p in problems if not p.startswith("!")]
    manual = [p[1:] for p in problems if p.startswith("!")]
    for p in auto:
        print(("MISMATCH " if ARGS.check else "aligned  ") + p)
    for p in manual:
        print("BY HAND  " + p)

    verb = "to align" if ARGS.check else "aligned"
    print(f"{len(seq)} lessons, {len(auto)} {verb}, {len(manual)} for a person")
    return 1 if problems and ARGS.check else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only, exit 1 on mismatch")
    ARGS = parser.parse_args()
    sys.exit(main())
