"""Assemble the context window for one model call. Nothing goes in by accident (lesson 08).

Layout, stable things first: system prompt, then the skill catalog (both cacheable),
then the thread history trimmed to the token budget by dropping the oldest whole
turns. Large tool results are shaped before the model sees them; the thread keeps
the full text.
"""

import json
from dataclasses import dataclass, field

from aiapp.adapters.base import Message
from aiapp.thread import Thread

SHAPE_OVER_CHARS = 4_000


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def shape_tool_result(content: str, *, head: int = 1_500, tail: int = 500) -> str:
    """Head, tail, and how much was left out. The thread still has everything."""
    if len(content) <= SHAPE_OVER_CHARS:
        return content
    omitted = len(content) - head - tail
    return f"{content[:head]}\n... [{omitted} chars omitted; full result is in the thread] ...\n{content[-tail:]}"


@dataclass
class ContextReport:
    system_tokens: int = 0
    catalog_tokens: int = 0
    history_tokens: int = 0
    dropped_messages: int = 0
    shaped_results: int = 0

    def as_dict(self) -> dict[str, int]:
        return self.__dict__.copy()


@dataclass
class ContextBuilder:
    system_prompt: str
    budget_tokens: int = 24_000
    skill_catalog: str = ""
    report: ContextReport = field(default_factory=ContextReport)

    def build(self, thread: Thread) -> list[Message]:
        system = self.system_prompt if not self.skill_catalog else f"{self.system_prompt}\n\n{self.skill_catalog}"
        fixed = [Message(role="system", content=system)]
        report = ContextReport(system_tokens=estimate_tokens(self.system_prompt), catalog_tokens=estimate_tokens(self.skill_catalog))
        spent = report.system_tokens + report.catalog_tokens
        if spent > self.budget_tokens:
            raise ValueError(f"system prompt and catalog alone use {spent} tokens; budget is {self.budget_tokens}")

        history = [self._shape(m, report) for m in thread.to_messages()]
        turns = _split_turns(history)
        kept: list[Message] = []
        for turn in reversed(turns):
            cost = sum(estimate_tokens(m.content) + 12 * len(m.tool_calls) for m in turn)
            if spent + cost > self.budget_tokens and kept:
                break
            kept = turn + kept
            spent += cost
        report.history_tokens = spent - report.system_tokens - report.catalog_tokens
        report.dropped_messages = len(history) - len(kept)
        self.report = report
        return fixed + kept

    def _shape(self, m: Message, report: ContextReport) -> Message:
        if m.role == "tool" and len(m.content) > SHAPE_OVER_CHARS:
            report.shaped_results += 1
            return Message(role="tool", tool_call_id=m.tool_call_id, content=shape_tool_result(m.content), is_error=m.is_error)
        return m


def _split_turns(messages: list[Message]) -> list[list[Message]]:
    """A turn starts at a user message and runs until the next one. Dropping whole turns keeps tool call/result pairs intact."""
    turns: list[list[Message]] = []
    for m in messages:
        if m.role == "user" or not turns:
            turns.append([m])
        else:
            turns[-1].append(m)
    return turns


def compact_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))
