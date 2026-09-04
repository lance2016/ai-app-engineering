"""Progressive disclosure: the model sees skill *names* first, bodies only on demand.

Level 1: every skill's name and description go into the system prompt (cheap).
Level 2: when the model picks a skill, the runtime loads that SKILL.md body.
Level 3: a skill may point at extra files; those load only when asked for.
Token counts at each level show why this matters once you have dozens of skills.

Run:  uv run python lessons/12-skills-and-capability-layers/code/01_progressive_loading.py
      INJECT_UNKNOWN_SKILL=1 uv run python lessons/12-skills-and-capability-layers/code/01_progressive_loading.py
Expect: three loading levels with growing token counts; with injection the model
        asks for a skill that does not exist and gets an error result, not a crash.
"""

# %% imports
import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from aiapp import FakeAdapter, Message, ModelResponse, ToolSpec, tool_call_response

SKILLS_DIR = Path(__file__).parent / "skills"
INJECT_UNKNOWN_SKILL = os.environ.get("INJECT_UNKNOWN_SKILL") == "1"


# %% skill_metadata
@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path

    def body(self) -> str:
        text = self.path.read_text(encoding="utf-8")
        return text.split("---", 2)[2].strip()  # everything after the frontmatter

    def reference(self, rel: str) -> str:
        target = (self.path.parent / rel).resolve()
        if self.path.parent.resolve() not in target.parents:
            raise PermissionError(f"{rel} escapes the skill directory")
        return target.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    _, fm, _ = text.split("---", 2)
    return {k.strip(): v.strip() for k, v in (line.split(":", 1) for line in fm.strip().splitlines() if ":" in line)}


def discover(skills_dir: Path) -> dict[str, Skill]:
    skills = {}
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        skills[fm["name"]] = Skill(fm["name"], fm["description"], skill_md)
    return skills


def tokens(text: str) -> int:
    return max(1, len(text) // 4)


# %% level_1_prompt
def level1_prompt(skills: dict[str, Skill]) -> str:
    lines = ["You have these skills. Call load_skill(name) before using one."]
    lines += [f"- {s.name}: {s.description}" for s in skills.values()]
    return "\n".join(lines)


LOAD_SKILL = ToolSpec("load_skill", "Load a skill's full instructions.", {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]})
READ_REF = ToolSpec("read_skill_reference", "Read a file referenced by the loaded skill.", {"type": "object", "properties": {"skill": {"type": "string"}, "path": {"type": "string"}}, "required": ["skill", "path"]})


# %% run
async def main() -> None:
    skills = discover(SKILLS_DIR)
    system = level1_prompt(skills)
    print(f"level 1: {len(skills)} skills advertised, ~{tokens(system)} tokens")
    wanted = "nonexistent-skill" if INJECT_UNKNOWN_SKILL else "expense-report"
    script = [tool_call_response("load_skill", {"name": wanted})]
    if INJECT_UNKNOWN_SKILL:
        script.append(ModelResponse(content="I do not have a skill for that; here is a plain review instead."))
    else:
        script += [
            tool_call_response("read_skill_reference", {"skill": "expense-report", "path": "references/policy.md"}),
            ModelResponse(content="Hotel 650 is over the 600 tier-1 limit; the rest is approved."),
        ]
    model = FakeAdapter(script=script)
    messages = [Message(role="system", content=system), Message(role="user", content="Review: hotel 650, dinner 45, beer 12.")]
    loaded_tokens = tokens(system)
    for _ in range(4):
        reply = await model.complete(messages, tools=[LOAD_SKILL, READ_REF])
        if not reply.wants_tool:
            print(f"assistant: {reply.content}")
            break
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            if call.name == "load_skill":
                skill = skills.get(call.arguments["name"])
                if skill is None:
                    content, err = f"unknown skill: {call.arguments['name']}", True
                else:
                    content, err = skill.body(), False
                    loaded_tokens += tokens(content)
                    print(f"level 2: loaded {skill.name} body, ~{tokens(content)} tokens (total ~{loaded_tokens})")
            else:
                skill = skills[call.arguments["skill"]]
                try:
                    content, err = skill.reference(call.arguments["path"]), False
                    loaded_tokens += tokens(content)
                    print(f"level 3: loaded {call.arguments['path']}, ~{tokens(content)} tokens (total ~{loaded_tokens})")
                except (PermissionError, FileNotFoundError) as exc:
                    content, err = str(exc), True
            if err:
                print(f"tool {call.name} -> [ERROR] {content}")
            messages.append(Message(role="tool", tool_call_id=call.id, content=content, is_error=err))


if __name__ == "__main__":
    asyncio.run(main())
