"""Fail if a relative Markdown link is broken, or mislabelled with a lesson number.

Run:  uv run python scripts/check_links.py
Scans every .md file in the repo (except templates/, whose links are
placeholders). External links (http, mailto) and pure anchors are skipped.

Two checks. The first is that the target exists. The second is that a link
written as `[14 RAG 端到端](../rag-end-to-end/README.md)` names the number that
lesson actually has. Directories carry no number any more -- the nav in
mkdocs.yml does -- so a lesson inserted in the middle leaves labels all over
the repo naming whichever lesson used to sit at that number, and a check that
only resolves paths stays green through it. Exit code 1 when either fails.
"""

import re
import sys
from pathlib import Path

from sync_numbering import order

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", ".pytest_cache", "templates"}
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
# [NN 标题](.../slug/README.md) -- the label's number must match the nav's.
NUMBERED_RE = re.compile(r"\[(\d{2})[^\]]*\]\([^)]*?([a-z0-9-]+)/README\.md")
NUMBER_OF = {slug: f"{i:02d}" for i, slug in enumerate(order())}
# Fenced code blocks contain regexes and shell that look like links; skip them.
FENCE_RE = re.compile(r"^```", re.MULTILINE)


def iter_markdown() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return sorted(files)


def is_local(target: str) -> bool:
    return not (target.startswith(("http://", "https://", "mailto:", "#")) or "://" in target)


def strip_code_blocks(text: str) -> str:
    """Drop fenced blocks so regexes and shell snippets are not read as links."""
    parts = text.split("```")
    return "".join(parts[::2])  # keep the segments outside the fences


def broken_links(md: Path) -> list[str]:
    text = strip_code_blocks(md.read_text(encoding="utf-8"))
    bad = []
    for target in LINK_RE.findall(text):
        if not is_local(target):
            continue
        path_part = target.split("#", 1)[0]
        if not path_part:
            continue
        resolved = (md.parent / path_part).resolve()
        if not resolved.exists():
            bad.append(target)
    return bad


def mislabelled(md: Path) -> list[str]:
    """Links whose label names a different lesson than the one they point at."""
    text = strip_code_blocks(md.read_text(encoding="utf-8"))
    bad = []
    for label, slug in NUMBERED_RE.findall(text):
        want = NUMBER_OF.get(slug)   # not a lesson (a prerequisite, say): skip
        if want and label != want:
            bad.append(f"[{label} ...] -> {slug}, which is {want}")
    return bad


def main() -> int:
    files = iter_markdown()
    broken = labels = 0
    for md in files:
        rel = md.relative_to(ROOT)
        for target in broken_links(md):
            print(f"BROKEN {rel} -> {target}")
            broken += 1
        for note in mislabelled(md):
            print(f"LABEL  {rel}: {note}")
            labels += 1
    print(f"checked {len(files)} files, {broken} broken link(s), {labels} mislabelled")
    return 1 if broken or labels else 0


if __name__ == "__main__":
    sys.exit(main())
