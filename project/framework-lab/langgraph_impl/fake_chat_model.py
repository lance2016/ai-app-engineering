"""A LangChain chat model that replays the course's FakeAdapter script, so LangGraph runs offline and deterministically."""

import json
from typing import Any

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import ConfigDict

from aiapp import FakeAdapter, Message, ToolCall


def to_aiapp(messages: list[BaseMessage]) -> list[Message]:
    out: list[Message] = []
    for m in messages:
        if isinstance(m, SystemMessage):
            out.append(Message(role="system", content=str(m.content)))
        elif isinstance(m, HumanMessage):
            out.append(Message(role="user", content=str(m.content)))
        elif isinstance(m, AIMessage):
            calls = tuple(ToolCall(id=c["id"], name=c["name"], arguments=dict(c["args"])) for c in m.tool_calls)
            out.append(Message(role="assistant", content=str(m.content), tool_calls=calls))
        elif isinstance(m, ToolMessage):
            out.append(Message(role="tool", tool_call_id=m.tool_call_id, content=str(m.content), is_error=m.status == "error"))
    return out


class ScriptedChatModel(BaseChatModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    fake: FakeAdapter

    @property
    def _llm_type(self) -> str:
        return "aiapp-fake"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "ScriptedChatModel":
        return self  # the script already knows which tools it will call

    def _generate(self, messages: list[BaseMessage], stop: list[str] | None = None, run_manager: CallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        raise NotImplementedError("async only: the graph nodes await ainvoke")

    async def _agenerate(self, messages: list[BaseMessage], stop: list[str] | None = None, run_manager: AsyncCallbackManagerForLLMRun | None = None, **kwargs: Any) -> ChatResult:
        reply = await self.fake.complete(to_aiapp(messages))
        ai = AIMessage(
            content=reply.content,
            tool_calls=[{"name": c.name, "args": c.arguments, "id": c.id, "type": "tool_call"} for c in reply.tool_calls],
            usage_metadata={"input_tokens": reply.usage.input_tokens, "output_tokens": reply.usage.output_tokens, "total_tokens": reply.usage.input_tokens + reply.usage.output_tokens},
        )
        return ChatResult(generations=[ChatGeneration(message=ai)])


def dump_args(args: dict) -> str:
    return json.dumps(args, ensure_ascii=False, sort_keys=True)
