"""Skills: reusable instructions loaded on demand (lesson 12). Names always, bodies when asked, references when asked again."""

import re
from dataclasses import dataclass
from pathlib import Path

from aiapp.adapters.base import ToolSpec
from aiapp.runtime.registry import Tool, ToolRegistry

LOAD_SKILL = "load_skill"
READ_SKILL_REFERENCE = "read_skill_reference"
SKILL_TOOLS = frozenset({LOAD_SKILL, READ_SKILL_REFERENCE})


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    version: str
    path: Path

    def body(self) -> str:
        return self.path.read_text(encoding="utf-8").split("---", 2)[2].strip()

    def reference(self, rel: str) -> str:
        target = (self.path.parent / rel).resolve()
        if self.path.parent.resolve() not in target.parents:
            raise ValueError(f"{rel} escapes the skill directory")
        if not target.is_file():
            raise ValueError(f"{rel} is not a file in skill {self.name}")
        return target.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    _, fm, _ = text.split("---", 2)
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in fm.strip().splitlines() if ":" in line)}


def validate_skill(skill_dir: Path, registry_tools: frozenset[str]) -> list[str]:
    """Problems that block installation. Warnings start with 'warning:' and do not block."""
    problems: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return ["missing SKILL.md"]
    fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    for field_name in ("name", "description"):
        if field_name not in fm:
            problems.append(f"missing {field_name}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", fm.get("name", "")):
        problems.append(f"name {fm.get('name')!r} is not a kebab-case slug")
    if fm.get("name") != skill_dir.name:
        problems.append(f"name {fm.get('name')!r} != directory {skill_dir.name!r}")
    if len(fm.get("description", "")) > 300:
        problems.append("description over 300 chars; it is loaded into every prompt")
    unknown = {t.strip() for t in fm.get("allowed-tools", "").split(",") if t.strip()} - registry_tools
    if unknown:
        problems.append(f"warning: allowed-tools not in registry: {sorted(unknown)}")
    return problems


class SkillLoader:
    def __init__(self, root: Path):
        self.root = root
        self.skills: dict[str, Skill] = {}
        self.rejected: dict[str, list[str]] = {}

    def discover(self, registry_tools: frozenset[str] = frozenset()) -> "SkillLoader":
        self.skills, self.rejected = {}, {}
        if not self.root.exists():
            return self
        for skill_dir in sorted(p for p in self.root.iterdir() if p.is_dir()):
            problems = validate_skill(skill_dir, registry_tools)
            blocking = [p for p in problems if not p.startswith("warning")]
            if blocking:
                self.rejected[skill_dir.name] = blocking
                continue
            fm = parse_frontmatter((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
            self.skills[fm["name"]] = Skill(fm["name"], fm["description"], fm.get("version", "0"), skill_dir / "SKILL.md")
        return self

    def catalog(self) -> str:
        """Level 1: names and descriptions only. Goes into the (cacheable) system prompt."""
        if not self.skills:
            return ""
        lines = [f"You have these skills. Call {LOAD_SKILL}(name) before using one; never guess a skill's procedure."]
        lines += [f"- {s.name}: {s.description}" for s in self.skills.values()]
        return "\n".join(lines)

    def load(self, name: str) -> str:
        skill = self.skills.get(name)
        if skill is None:
            raise ValueError(f"unknown skill: {name}; available: {sorted(self.skills)}")
        return skill.body()

    def reference(self, name: str, rel: str) -> str:
        skill = self.skills.get(name)
        if skill is None:
            raise ValueError(f"unknown skill: {name}")
        return skill.reference(rel)

    def register_into(self, registry: ToolRegistry) -> None:
        """Levels 2 and 3 are ordinary read-only tools; the runner validates and traces them like any other."""
        registry.register(Tool(
            ToolSpec(LOAD_SKILL, "Load a skill's full instructions by name.", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}),
            lambda a: self.load(a["name"]),
        ))
        registry.register(Tool(
            ToolSpec(READ_SKILL_REFERENCE, "Read a file referenced by a loaded skill.", {"type": "object", "properties": {"skill": {"type": "string"}, "path": {"type": "string"}}, "required": ["skill", "path"]}),
            lambda a: self.reference(a["skill"], a["path"]),
        ))
