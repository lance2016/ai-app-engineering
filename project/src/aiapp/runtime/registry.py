"""The tool registry: what exists, what this request may see, and whether a call is well-formed.

A tool is a spec (what the model is told), a handler (what actually runs) and
a flag saying whether it changes the world. Validation happens here, before
anything runs; an invalid call becomes an error *result* the model can read.
"""

import inspect
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from aiapp.adapters.base import ToolCall, ToolSpec

Handler = Callable[[dict[str, Any]], str | Awaitable[str]]

JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Handler
    has_side_effects: bool = False
    args_model: type[BaseModel] | None = None  # when given, Pydantic validates; otherwise the JSON schema's required/types do

    def validate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Return validated arguments or raise ValueError with a message the model can act on."""
        if self.args_model is not None:
            try:
                return self.args_model.model_validate(arguments).model_dump()
            except ValidationError as exc:
                first = exc.errors()[0]
                where = ".".join(str(p) for p in first["loc"]) or "arguments"
                raise ValueError(f"invalid arguments: {where}: {first['msg']}") from None
        schema = self.spec.parameters
        missing = [k for k in schema.get("required", []) if k not in arguments]
        if missing:
            raise ValueError(f"invalid arguments: missing required {missing}")
        for key, value in arguments.items():
            expected = schema.get("properties", {}).get(key, {}).get("type")
            if expected in JSON_TYPES and not isinstance(value, JSON_TYPES[expected]) or (expected == "integer" and isinstance(value, bool)):
                raise ValueError(f"invalid arguments: {key} should be {expected}, got {type(value).__name__}")
        return arguments

    async def execute(self, arguments: dict[str, Any]) -> str:
        result = self.handler(arguments)
        if inspect.isawaitable(result):
            result = await result
        return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.spec.name in self._tools:
            raise ValueError(f"tool {tool.spec.name!r} is already registered")
        self._tools[tool.spec.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> frozenset[str]:
        return frozenset(self._tools)

    def specs(self, allowlist: frozenset[str]) -> list[ToolSpec]:
        """Only advertise what this request may use. The model cannot pick what it cannot see."""
        return [t.spec for name, t in self._tools.items() if name in allowlist]

    def __len__(self) -> int:
        return len(self._tools)


def signature(call: ToolCall) -> str:
    """Same tool + same canonical arguments => same signature. Used for off-track detection and idempotency."""
    return f"{call.name}:{json.dumps(call.arguments, sort_keys=True, separators=(',', ':'), ensure_ascii=False)}"
