"""Sync status columns in the overview tables from each file's frontmatter.

Run:  uv run python scripts/sync_status.py
It rewrites the status cell of every table row that links to a lesson,
principle, prerequisite module or project milestone, using the `status:`
value in that file's frontmatter. The frontmatter is the source of truth.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUSES = ("outline", "draft", "complete")
TABLES = [ROOT / "README.md", ROOT / "principles/README.md", ROOT / "prerequisites/README.md", ROOT / "project/README.md"]
LINK_RE = re.compile(r"\]\((\./[^)#\s]+)\)")
STATUS_CELL_RE = re.compile(r"\| (outline|draft|complete) \|\s*$")


def frontmatter_status(path: Path) -> str | None:
    if path.is_dir():
        path = path / "README.md"
    if not path.exists():
        return None
    head = path.read_text(encoding="utf-8")[:400]
    m = re.search(r"^status:\s*(\w+)", head, re.M)
    return m.group(1) if m else None


def sync_table(table: Path) -> int:
    changed = 0
    lines = table.read_text(encoding="utf-8").split("\n")
    for i, line in enumerate(lines):
        if not line.startswith("|") or not STATUS_CELL_RE.search(line):
            continue
        link = LINK_RE.search(line)
        if not link:
            continue
        status = frontmatter_status((table.parent / link.group(1)).resolve())
        if status not in STATUSES:
            continue
        new = STATUS_CELL_RE.sub(f"| {status} |", line)
        if new != line:
            lines[i] = new
            changed += 1
    if changed:
        table.write_text("\n".join(lines), encoding="utf-8")
    return changed


if __name__ == "__main__":
    for t in TABLES:
        print(f"{t.relative_to(ROOT)}: {sync_table(t)} row(s) updated")
