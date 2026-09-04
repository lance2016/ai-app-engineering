"""The knowledge tool: search_knowledge(query) returns sources keyed by citation id, scoped to the caller's tenant.

The handler takes ``ctx`` so the tenant filter comes from the run, never from
the model's arguments. Sources are returned as JSON so the runtime can rebuild
them from the tool_result event and verify the model's citations afterwards.
"""

import json

from pydantic import BaseModel, Field

from aiapp.adapters.base import ToolSpec
from aiapp.knowledge.base import Hit
from aiapp.knowledge.retriever import Retriever
from aiapp.runtime.registry import Tool, ToolRegistry
from aiapp.runtime.runner import RunContext

SEARCH_KNOWLEDGE = "search_knowledge"
CITATION_INSTRUCTIONS = (
    "When you answer from search_knowledge results, cite the source after each sentence as [citation_id] using the ids returned. "
    "Only cite ids you actually received. If the sources do not contain the answer, say so."
)


class SearchKnowledgeArgs(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=5, ge=1, le=10)


def hits_to_sources(hits: list[Hit]) -> list[dict]:
    return [{"citation_id": h.citation_id, "doc_id": h.doc_id, "version": h.version, "section": h.section, "text": h.text.strip()} for h in hits]


def sources_from_tool_result(content: str) -> dict[str, str]:
    """{citation_id: text} from a search_knowledge tool_result; empty if the content is not one of ours."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict) or "sources" not in data:
        return {}
    return {s["citation_id"]: s["text"] for s in data["sources"]}


def register_knowledge_tool(registry: ToolRegistry, retriever: Retriever) -> None:
    async def search(arguments: dict, ctx: RunContext) -> str:
        hits = await retriever.search(arguments["query"], tenant_id=ctx.tenant_id, k=arguments.get("k", 5))
        return json.dumps({"query": arguments["query"], "sources": hits_to_sources(hits)}, ensure_ascii=False)

    registry.register(Tool(
        ToolSpec(SEARCH_KNOWLEDGE, "Search the tenant's knowledge base. Returns sources with citation ids to cite as [citation_id].", SearchKnowledgeArgs.model_json_schema()),
        search,
        args_model=SearchKnowledgeArgs,
    ))
