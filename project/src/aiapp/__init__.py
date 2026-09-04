"""Shared runtime pieces used by every lesson's code samples.

Kept deliberately small: message and tool types, a model adapter protocol,
and a scripted fake adapter so all lessons run without an API key.
"""

from aiapp.adapters import get_adapter
from aiapp.adapters.base import Message, ModelAdapter, ModelResponse, StreamChunk, ToolCall, ToolSpec, Usage
from aiapp.adapters.fake import FakeAdapter, tool_call_response
from aiapp.thread import Event, Thread, tool_calls_as_data

__all__ = [
    "Event",
    "Thread",
    "tool_calls_as_data",
    "FakeAdapter",
    "Message",
    "ModelAdapter",
    "ModelResponse",
    "StreamChunk",
    "ToolCall",
    "ToolSpec",
    "Usage",
    "get_adapter",
    "tool_call_response",
]
