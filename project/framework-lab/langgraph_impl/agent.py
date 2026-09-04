"""The approval agent as a LangGraph StateGraph: agent node <-> tools node, interrupts for humans, SQLite checkpoints.

What LangGraph gives for free: the checkpoint after every node, ``interrupt()`` for
both the question and the confirmation, resume with ``Command(resume=...)`` on any
later process, ``recursion_limit`` as the step cap. What it does not give: tool
validation, allowlists, idempotency (we reuse aiapp's ``Tool`` for the first).
"""

from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import interrupt

from aiapp.runtime import ToolRegistry
from aiapp.tools.demo import DocStore
from langgraph_impl.fake_chat_model import ScriptedChatModel

SYSTEM = "You are a document workspace assistant."
REQUEST_HUMAN_INPUT = "request_human_input"


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    steps: int


def build_graph(model: ScriptedChatModel, docs: DocStore, checkpointer):
    registry = ToolRegistry()
    docs.register_into(registry)

    async def agent(state: AgentState) -> dict[str, Any]:
        reply = await model.ainvoke([SystemMessage(content=SYSTEM), *state["messages"]])
        return {"messages": [reply], "steps": state.get("steps", 0) + 1}

    async def tools(state: AgentState) -> dict[str, Any]:
        last = state["messages"][-1]
        assert isinstance(last, AIMessage)
        results: list[ToolMessage] = []
        for call in last.tool_calls:
            name, args, call_id = call["name"], dict(call["args"]), call["id"]
            if name == REQUEST_HUMAN_INPUT:
                # The node pauses here; on resume it re-runs from the top and interrupt() returns the answer.
                answer = interrupt({"kind": "question", "question": args.get("question", ""), "id": call_id})
                results.append(ToolMessage(content=str(answer), tool_call_id=call_id, name=name))
                continue
            tool = registry.get(name)
            if tool is None:
                results.append(ToolMessage(content=f"unknown tool: {name}", tool_call_id=call_id, name=name, status="error"))
                continue
            try:
                arguments = tool.validate(args)
            except ValueError as exc:
                results.append(ToolMessage(content=str(exc), tool_call_id=call_id, name=name, status="error"))
                continue
            if tool.has_side_effects:
                approved = interrupt({"kind": "confirmation", "tool": name, "arguments": arguments, "id": call_id})
                if not approved:
                    results.append(ToolMessage(content="user declined; nothing was changed", tool_call_id=call_id, name=name, status="error"))
                    continue
            try:
                results.append(ToolMessage(content=await tool.execute(arguments), tool_call_id=call_id, name=name))
            except Exception as exc:  # noqa: BLE001 - a tool failure is a result the model reads
                results.append(ToolMessage(content=f"{name} failed: {exc}", tool_call_id=call_id, name=name, status="error"))
        return {"messages": results}

    def route(state: AgentState) -> str:
        last = state["messages"][-1]
        return "tools" if isinstance(last, AIMessage) and last.tool_calls else END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)
