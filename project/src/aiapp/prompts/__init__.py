"""Versioned system prompts. A prompt is a file named <name>.<version>.md next to this module.

Versioning the file, not the string, means a change is a diff in git and the
version in use can be reported on every response (M1 sends it as a header).
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def available_versions(name: str) -> list[str]:
    return sorted(p.name.split(".")[1] for p in PROMPTS_DIR.glob(f"{name}.*.md"))


def load_prompt(name: str, version: str) -> str:
    path = PROMPTS_DIR / f"{name}.{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt {name}.{version}.md not found; available versions: {available_versions(name)}")
    return path.read_text(encoding="utf-8").strip()
