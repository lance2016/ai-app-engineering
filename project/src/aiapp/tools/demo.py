"""A small document workspace: three tools that exercise every path of the runner.

``search_docs`` and ``read_doc`` are read-only. ``delete_doc`` changes the world,
so the runner will pause for confirmation before running it. ``FlakySearch``
fails transiently on demand so tests and demos can rehearse the retry path.
"""

import json
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

from aiapp.adapters.base import ToolSpec
from aiapp.runtime.errors import TransientToolError
from aiapp.runtime.registry import Tool, ToolRegistry

DEFAULT_DOCS = {
    "doc_refunds": "Refund policy: full refund within 30 days with receipt; store credit after that.",
    "doc_shipping": "Shipping: orders over 50 ship free; otherwise a flat 6. International adds 3 to 7 business days.",
    "doc_returns_draft": "DRAFT returns process v0: do not publish.",
}


class SearchArgs(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=5, ge=1, le=20)


class ReadArgs(BaseModel):
    doc_id: str


class DeleteArgs(BaseModel):
    doc_id: str
    reason: Literal["obsolete", "duplicate", "draft"] = "obsolete"


@dataclass
class DocStore:
    docs: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_DOCS))
    fail_next_searches: int = 0  # failure injection: the next N searches raise a transient error
    deleted: list[str] = field(default_factory=list)

    def search(self, args: dict) -> str:
        if self.fail_next_searches > 0:
            self.fail_next_searches -= 1
            raise TransientToolError("search backend connection reset")
        q = args["query"].lower()
        hits = [{"doc_id": d, "snippet": t[:80]} for d, t in self.docs.items() if q in t.lower() or q in d]
        return json.dumps(hits[: args.get("limit", 5)], ensure_ascii=False)

    def read(self, args: dict) -> str:
        text = self.docs.get(args["doc_id"])
        if text is None:
            raise ValueError(f"no such document: {args['doc_id']}")
        return text

    def delete(self, args: dict) -> str:
        if args["doc_id"] not in self.docs:
            raise ValueError(f"no such document: {args['doc_id']}")
        del self.docs[args["doc_id"]]
        self.deleted.append(args["doc_id"])
        return f"deleted {args['doc_id']} ({args.get('reason', 'obsolete')})"

    def register_into(self, registry: ToolRegistry) -> None:
        registry.register(Tool(ToolSpec("search_docs", "Search the document workspace by keyword.", SearchArgs.model_json_schema()), self.search, args_model=SearchArgs))
        registry.register(Tool(ToolSpec("read_doc", "Read one document by id.", ReadArgs.model_json_schema()), self.read, args_model=ReadArgs))
        registry.register(Tool(ToolSpec("delete_doc", "Delete a document by id. Irreversible.", DeleteArgs.model_json_schema()), self.delete, has_side_effects=True, args_model=DeleteArgs))


def build_default_registry(store: DocStore | None = None) -> tuple[ToolRegistry, DocStore]:
    store = store or DocStore()
    registry = ToolRegistry()
    store.register_into(registry)
    return registry, store
