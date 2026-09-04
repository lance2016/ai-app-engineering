"""Request and response shapes. Pydantic validates on the way in and documents on the way out."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aiapp.thread import Thread


class CreateThreadRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, max_length=200)


class MessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=20_000)
    allowed_tools: list[str] | None = Field(default=None, description="Narrow this request's tools; never widens the server allowlist")


class HumanInputRequest(BaseModel):
    """Either answer a question (tool_call_id + content) or decide on a confirmation (confirm_tool_call_id + approved)."""

    model_config = ConfigDict(extra="forbid")
    tool_call_id: str | None = None
    content: str | None = Field(default=None, max_length=20_000)
    confirm_tool_call_id: str | None = None
    approved: bool | None = None


class EventView(BaseModel):
    type: str
    data: dict[str, Any]
    ts: float


class ThreadView(BaseModel):
    thread_id: str
    tenant_id: str
    status: str
    events: list[EventView]

    @classmethod
    def from_thread(cls, thread: Thread, tenant_id: str) -> "ThreadView":
        return cls(
            thread_id=thread.thread_id,
            tenant_id=tenant_id,
            status=thread.status(),
            events=[EventView(type=e.type, data=e.data, ts=e.ts) for e in thread.events],
        )
