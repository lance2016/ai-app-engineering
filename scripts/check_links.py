"""Fail if any relative Markdown link points to a missing file.

Run:  uv run python scripts/check_links.py
Scans every .md file in the repo (except templates/, whose links are
placeholders). External links (http, mailto) and pure anchors are skipped.
Exit code 1 when at least one link is broken.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules", ".pytest_cache", "templates"}
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
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


def main() -> int:
    failures = 0
    for md in iter_markdown():
        for target in broken_links(md):
            print(f"BROKEN {md.relative_to(ROOT)} -> {target}")
            failures += 1
    print(f"checked {len(iter_markdown())} files, {failures} broken link(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
