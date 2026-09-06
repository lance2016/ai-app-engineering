"""Fail if a relative Markdown link is broken, or mislabelled with a lesson number.

Run:  uv run python scripts/check_links.py
Scans every .md file in the repo (except templates/, whose links are
placeholders). External links (http, mailto) and pure anchors are skipped.

Two checks. The first is that the target exists. The second is that a link
written as `[14 RAG 端到端](../14-rag-end-to-end/README.md)` agrees with itself:
the 2026-09-06 renumber moved paths but left seven labels naming the old
lesson, and a check that only resolves paths stays green through that.
Exit code 1 when either fails.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", ".pytest_cache", "templates"}
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
# [NN 标题](../NN-slug/...) -- the label's lesson number must match the path's.
NUMBERED_RE = re.compile(r"\[(\d{2})[^\]]*\]\((?:\.\./)+(\d{2})-[a-z0-9-]+/")
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
    """Links whose label names a different lesson than the path they point at."""
    text = strip_code_blocks(md.read_text(encoding="utf-8"))
    return [f"[{label} ...] -> {path}-..." for label, path in NUMBERED_RE.findall(text) if label != path]


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
