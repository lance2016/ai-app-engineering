"""Long-term memories are extracted from the thread, and every one carries provenance.

A memory without a source is a rumour: you cannot verify it, cannot explain it
to the user, and cannot delete it when they ask "forget what I said about X".
The extractor here is the fake model returning structured output; the runtime
insists each candidate points at the event ids it came from.

Run:  uv run python lessons/14-memory/code/01_extract_with_provenance.py
      INJECT_NO_PROVENANCE=1 uv run python lessons/14-memory/code/01_extract_with_provenance.py
Expect: three memories stored with source event ids; with injection the
        extractor omits sources and the runtime rejects the batch.
"""

# %% imports
import asyncio
import json
import os
import tempfile
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from aiapp import FakeAdapter, Message, ModelResponse, Thread

INJECT_NO_PROVENANCE = os.environ.get("INJECT_NO_PROVENANCE") == "1"
STORE = Path(os.environ.get("MEMORY_DIR", tempfile.gettempdir())) / "aiapp_lesson14_memories.json"


# %% schema
class MemoryCandidate(BaseModel):
    content: str
    kind: str = Field(pattern="^(preference|fact|episode)$")
    source_event_ids: list[int] = Field(min_length=1)  # indexes into thread.events


class ExtractionResult(BaseModel):
    memories: list[MemoryCandidate]


# %% conversation
def build_thread() -> Thread:
    t = Thread(thread_id="thr_u42_01")
    t.append("user_message", content="Can you recommend a restaurant for Friday?")
    t.append("assistant_message", content="Sure. Any preferences?")
    t.append("user_message", content="Nothing spicy, I can't handle it. And my daughter is vegetarian.")
    t.append("assistant_message", content="Got it. How about Sea Breeze, it has a good vegetarian menu.")
    t.append("user_message", content="We tried Sea Breeze last month, the service was slow. Somewhere else please.")
    return t


def numbered_transcript(t: Thread) -> str:
    return "\n".join(f"[{i}] {e.type}: {e.data.get('content', '')}" for i, e in enumerate(t.events))


# %% extract
async def extract(thread: Thread, model: FakeAdapter) -> ExtractionResult:
    prompt = (
        "Extract durable facts about the user worth remembering across conversations. "
        "Return JSON {memories:[{content, kind, source_event_ids}]}. "
        "source_event_ids are the bracketed numbers of the lines the fact comes from.\n\n"
        + numbered_transcript(thread)
    )
    reply = await model.complete([Message(role="user", content=prompt)])
    try:
        return ExtractionResult.model_validate_json(reply.content)
    except ValidationError as exc:
        raise RuntimeError(f"extractor output rejected: {exc.errors()[0]['msg']} at {exc.errors()[0]['loc']}") from exc


def fake_extractor_output() -> str:
    memories = [
        {"content": "cannot eat spicy food", "kind": "preference", "source_event_ids": [2]},
        {"content": "has a vegetarian daughter", "kind": "fact", "source_event_ids": [2]},
        {"content": "visited Sea Breeze; found the service slow", "kind": "episode", "source_event_ids": [4]},
    ]
    if INJECT_NO_PROVENANCE:
        for m in memories:
            m["source_event_ids"] = []
    return json.dumps({"memories": memories})


# %% run
async def main() -> None:
    thread = build_thread()
    model = FakeAdapter(script=[ModelResponse(content=fake_extractor_output())])
    try:
        result = await extract(thread, model)
    except RuntimeError as exc:
        print(f"REJECTED: {exc}")
        print("nothing was stored; a memory that cannot say where it came from cannot be audited or deleted")
        return
    records = [
        {"user_id": "u42", "thread_id": thread.thread_id, **m.model_dump(), "source_text": [thread.events[i].data["content"] for i in m.source_event_ids]}
        for m in result.memories
    ]
    STORE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    for r in records:
        print(f"stored [{r['kind']}] {r['content']!r}  <- events {r['source_event_ids']}")
    print(f"{len(records)} memories written to {STORE}")


if __name__ == "__main__":
    asyncio.run(main())
