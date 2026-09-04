"""A skill is code you did not write, running with your tools. Validate it and pin it.

Validation: frontmatter has the required fields, the name is a safe slug, the
description is short enough to sit in every prompt, allowed-tools only names
tools your registry actually has. Pinning: record a content hash at install
time and refuse to load a skill whose files changed since.

Run:  uv run python lessons/12-skills-and-capability-layers/code/02_validate_and_pin.py
      INJECT_TAMPER=1 uv run python lessons/12-skills-and-capability-layers/code/02_validate_and_pin.py
Expect: both skills validate, one warning about a tool the registry lacks;
        with injection a reference file is modified after pinning and the load is refused.
"""

# %% imports
import hashlib
import os
import re
import shutil
import tempfile
from pathlib import Path

SKILLS_DIR = Path(__file__).parent / "skills"
INJECT_TAMPER = os.environ.get("INJECT_TAMPER") == "1"
REGISTRY_TOOLS = frozenset({"search_notes"})  # what this runtime actually offers (lesson 05 registry)


# %% validate
def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    _, fm, _ = text.split("---", 2)
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in fm.strip().splitlines() if ":" in line)}


def validate(skill_dir: Path) -> list[str]:
    """Return problems; an empty list means the skill may be installed."""
    problems: list[str] = []
    fm = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    for field in ("name", "description"):
        if field not in fm:
            problems.append(f"missing {field}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", fm.get("name", "")):
        problems.append(f"name {fm.get('name')!r} is not a kebab-case slug")
    if fm.get("name") != skill_dir.name:
        problems.append(f"name {fm.get('name')!r} != directory {skill_dir.name!r}")
    if len(fm.get("description", "")) > 300:
        problems.append("description over 300 chars; it is loaded into every prompt")
    unknown = {t.strip() for t in fm.get("allowed-tools", "").split(",") if t.strip()} - REGISTRY_TOOLS
    if unknown:
        problems.append(f"warning: allowed-tools not in registry: {sorted(unknown)}")
    return problems


# %% pin
def digest(skill_dir: Path) -> str:
    """Hash every file in the skill, in a stable order. This is the pin."""
    h = hashlib.sha256()
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(skill_dir)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:16]


def load_pinned(skill_dir: Path, pins: dict[str, str]) -> str:
    actual = digest(skill_dir)
    if pins.get(skill_dir.name) != actual:
        raise PermissionError(f"{skill_dir.name}: content hash {actual} != pinned {pins.get(skill_dir.name)}; refusing to load")
    return (skill_dir / "SKILL.md").read_text(encoding="utf-8")


# %% run
def main() -> None:
    work = Path(tempfile.mkdtemp()) / "skills"
    shutil.copytree(SKILLS_DIR, work)  # never mutate the lesson's own files
    pins: dict[str, str] = {}
    for skill_dir in sorted(p for p in work.iterdir() if p.is_dir()):
        problems = validate(skill_dir)
        blocking = [p for p in problems if not p.startswith("warning")]
        status = "rejected" if blocking else "ok"
        print(f"{skill_dir.name:16} {status:8} {problems or ''}")
        if not blocking:
            pins[skill_dir.name] = digest(skill_dir)
    print(f"pinned: {pins}")
    if INJECT_TAMPER:
        policy = work / "expense-report" / "references" / "policy.md"
        policy.write_text(policy.read_text().replace("Alcohol: not covered", "Alcohol: covered up to 500"))
        print("!! policy.md modified after install")
    try:
        load_pinned(work / "expense-report", pins)
        print("expense-report loaded: hash matches pin")
    except PermissionError as exc:
        print(f"load refused: {exc}")
    shutil.rmtree(work.parent)


if __name__ == "__main__":
    main()
