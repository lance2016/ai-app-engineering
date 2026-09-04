"""Per-user long-term memory: extracted with provenance, consolidated, retrieved per user, forgotten on request (lesson 14).

Three rules: a memory without source events is rejected; a newer statement on
the same subject supersedes the older one (kept as history, never shown); a
deletion is a soft delete with a reason, so "we forgot it" can be proven.
"""

import json
import uuid
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from aiapp.adapters.base import Message, ModelAdapter
from aiapp.adapters.embeddings import EmbeddingAdapter, cosine, tokenize
from aiapp.thread import Thread

KINDS = ("preference", "fact", "episode")


@dataclass(frozen=True)
class Memory:
    id: str
    tenant_id: str
    user_id: str
    content: str
    kind: str
    subject: str
    source_thread_id: str
    source_event_seqs: tuple[int, ...]
    created_at: datetime
    superseded_by: str | None = None
    active: bool = True
    deleted_reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id, "user_id": self.user_id, "content": self.content, "kind": self.kind, "subject": self.subject,
            "source_thread_id": self.source_thread_id, "source_event_seqs": list(self.source_event_seqs),
            "created_at": self.created_at.isoformat(), "superseded_by": self.superseded_by, "active": self.active,
        }


class MemoryStore(Protocol):
    async def add(self, memory: Memory, vector: list[float] | None, embedding_model: str | None) -> Memory: ...
    async def active_for(self, tenant_id: str, user_id: str) -> list[Memory]: ...
    async def search(self, tenant_id: str, user_id: str, query_vector: list[float] | None, query: str, *, k: int, embedding_model: str | None) -> list[Memory]: ...
    async def supersede(self, old_id: str, new_id: str) -> None: ...
    async def forget(self, tenant_id: str, user_id: str, *, subject: str | None = None, memory_id: str | None = None, reason: str) -> list[Memory]: ...
    async def history(self, tenant_id: str, user_id: str) -> list[Memory]:
        """Everything, including superseded and deleted rows: the audit view."""
        ...


# ---- extraction ----------------------------------------------------------------------------------
class MemoryCandidate(BaseModel):
    content: str = Field(min_length=3, max_length=500)
    kind: str = Field(pattern="^(preference|fact|episode)$")
    subject: str = Field(min_length=1, max_length=60)
    source_event_seqs: list[int] = Field(min_length=1)


class ExtractionResult(BaseModel):
    memories: list[MemoryCandidate]


class ExtractionRejected(ValueError):
    pass


EXTRACT_PROMPT = (
    "Extract durable facts about the user worth remembering across conversations: preferences, stable facts, notable episodes. "
    "Return only JSON: {\"memories\": [{\"content\", \"kind\": \"preference|fact|episode\", \"subject\": short-slug, \"source_event_seqs\": [ints]}]}. "
    "source_event_seqs are the bracketed numbers of the transcript lines the fact comes from. Skip anything the user did not say themselves."
)


def numbered_transcript(thread: Thread) -> str:
    return "\n".join(f"[{i}] {e.type}: {e.data.get('content', '')}" for i, e in enumerate(thread.events) if e.type in ("user_message", "assistant_message") and e.data.get("content"))


async def extract_candidates(thread: Thread, model: ModelAdapter) -> list[MemoryCandidate]:
    reply = await model.complete([Message(role="system", content=EXTRACT_PROMPT), Message(role="user", content=numbered_transcript(thread))])
    raw = reply.content.strip().strip("`").removeprefix("json").strip()
    try:
        result = ExtractionResult.model_validate_json(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        raise ExtractionRejected(f"extractor output rejected: {first['msg']} at {list(first['loc'])}") from None
    user_seqs = {i for i, e in enumerate(thread.events) if e.type == "user_message"}
    for c in result.memories:
        if not set(c.source_event_seqs) <= user_seqs:
            raise ExtractionRejected(f"memory {c.content!r} cites events {c.source_event_seqs} that are not user messages of this thread")
    return result.memories


# ---- service ----------------------------------------------------------------------------------------
@dataclass
class MemoryService:
    store: MemoryStore
    embedder: EmbeddingAdapter | None = None

    async def _vector(self, text: str) -> tuple[list[float] | None, str | None]:
        if self.embedder is None:
            return None, None
        return (await self.embedder.embed([text]))[0], self.embedder.name

    async def remember(self, tenant_id: str, user_id: str, thread: Thread, model: ModelAdapter) -> list[tuple[str, Memory]]:
        """Extract from the thread and consolidate into the store. Returns (outcome, memory) per candidate."""
        outcomes: list[tuple[str, Memory]] = []
        active = await self.store.active_for(tenant_id, user_id)
        for c in await extract_candidates(thread, model):
            memory = Memory(f"mem_{uuid.uuid4().hex[:8]}", tenant_id, user_id, c.content.strip(), c.kind, c.subject.strip().lower(), thread.thread_id, tuple(c.source_event_seqs), datetime.now(UTC))
            duplicate = next((m for m in active if m.content.lower() == memory.content.lower()), None)
            if duplicate:
                outcomes.append(("duplicate", duplicate))
                continue
            vector, model_name = await self._vector(memory.content)
            stored = await self.store.add(memory, vector, model_name)
            conflict = next((m for m in active if m.subject == memory.subject and m.kind != "episode" and memory.kind != "episode"), None)
            if conflict:
                await self.store.supersede(conflict.id, stored.id)
                active = [m for m in active if m.id != conflict.id]
                outcomes.append((f"superseded {conflict.id}", stored))
            else:
                outcomes.append(("added", stored))
            active.append(stored)
        return outcomes

    async def recall(self, tenant_id: str, user_id: str, query: str, *, k: int = 5) -> list[Memory]:
        vector, model_name = await self._vector(query)
        return await self.store.search(tenant_id, user_id, vector, query, k=k, embedding_model=model_name)

    async def forget(self, tenant_id: str, user_id: str, *, subject: str | None = None, memory_id: str | None = None, reason: str = "user request") -> list[Memory]:
        return await self.store.forget(tenant_id, user_id, subject=subject, memory_id=memory_id, reason=reason)


def render_memories(memories: list[Memory]) -> str:
    if not memories:
        return ""
    lines = ["What you remember about this user (each item was said by the user in an earlier conversation; phrase it as a recollection, not a fact about the world):"]
    lines += [f"- ({m.kind}) {m.content}" for m in memories]
    return "\n".join(lines)


# ---- in-memory store --------------------------------------------------------------------------------
@dataclass
class InMemoryMemoryStore:
    rows: dict[str, Memory] = field(default_factory=dict)
    vectors: dict[str, tuple[list[float] | None, str | None]] = field(default_factory=dict)

    async def add(self, memory: Memory, vector: list[float] | None, embedding_model: str | None) -> Memory:
        self.rows[memory.id] = memory
        self.vectors[memory.id] = (vector, embedding_model)
        return memory

    async def active_for(self, tenant_id: str, user_id: str) -> list[Memory]:
        return [m for m in self.rows.values() if m.tenant_id == tenant_id and m.user_id == user_id and m.active and m.superseded_by is None]

    async def search(self, tenant_id: str, user_id: str, query_vector, query: str, *, k: int, embedding_model) -> list[Memory]:
        active = await self.active_for(tenant_id, user_id)
        if len(active) <= k:
            return active  # few memories: relevance ranking cannot beat "show them all"; the filter matters once there are many
        words = set(tokenize(query))
        scored = []
        for m in active:
            vec, model_name = self.vectors.get(m.id, (None, None))
            score = cosine(query_vector, vec) if query_vector is not None and vec is not None and model_name == embedding_model else 0.0
            score += 0.5 * len(words & set(tokenize(m.content + " " + m.subject)))
            if score > 0:
                scored.append((score, m))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored[:k]]

    async def supersede(self, old_id: str, new_id: str) -> None:
        self.rows[old_id] = replace(self.rows[old_id], superseded_by=new_id)

    async def forget(self, tenant_id: str, user_id: str, *, subject=None, memory_id=None, reason: str) -> list[Memory]:
        removed = []
        for mid, m in list(self.rows.items()):
            if m.tenant_id != tenant_id or m.user_id != user_id or not m.active:
                continue
            if (memory_id and mid == memory_id) or (subject and m.subject == subject):
                self.rows[mid] = replace(m, active=False, deleted_reason=reason)
                removed.append(self.rows[mid])
        return removed

    async def history(self, tenant_id: str, user_id: str) -> list[Memory]:
        return [m for m in self.rows.values() if m.tenant_id == tenant_id and m.user_id == user_id]


def memory_audit(memories: list[Memory]) -> str:
    return json.dumps([{"id": m.id, "subject": m.subject, "reason": m.deleted_reason, "source_thread": m.source_thread_id, "source_event_seqs": list(m.source_event_seqs)} for m in memories], ensure_ascii=False)
