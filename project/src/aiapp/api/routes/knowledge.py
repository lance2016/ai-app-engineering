"""Documents in and out of the knowledge base; memories listed, extracted and forgotten. All tenant-scoped."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aiapp.adapters.base import ModelAdapter
from aiapp.api.deps import Tenant, get_memory, get_model, get_retriever, get_store, get_tenant, get_user_id
from aiapp.api.errors import InvalidRequest, NotFound
from aiapp.api.schemas import IngestDocumentRequest
from aiapp.knowledge.memory import ExtractionRejected, MemoryService, memory_audit
from aiapp.knowledge.retriever import Retriever
from aiapp.knowledge import parse_markdown
from aiapp.storage.base import ThreadNotFound, ThreadStore, flush

router = APIRouter(prefix="/v1", tags=["knowledge"])


@router.post("/documents", status_code=201)
async def ingest_document(
    body: IngestDocumentRequest,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    retriever: Annotated[Retriever, Depends(get_retriever)],
) -> dict:
    report = await retriever.ingest(tenant.id, parse_markdown(body.doc_id, body.text, version=body.version, title=body.title))
    return report.__dict__


@router.get("/documents")
async def list_documents(tenant: Annotated[Tenant, Depends(get_tenant)], retriever: Annotated[Retriever, Depends(get_retriever)]) -> list[dict]:
    return [{"doc_id": d, "version": v, "title": t} for d, v, t in await retriever.store.list_documents(tenant.id)]


@router.delete("/documents/{doc_id:path}")
async def delete_document(doc_id: str, tenant: Annotated[Tenant, Depends(get_tenant)], retriever: Annotated[Retriever, Depends(get_retriever)]) -> dict:
    """Delete the document and prove it: the response carries the residue count in every derived store."""
    removed = await retriever.store.delete_document(tenant.id, doc_id)
    if removed == 0:
        raise NotFound(f"document {doc_id} not found")
    return {"doc_id": doc_id, "removed_chunks": removed, "residue": await retriever.store.residue(tenant.id, doc_id)}


@router.get("/knowledge/search")
async def search_knowledge(
    q: Annotated[str, Query(min_length=1, max_length=500)],
    tenant: Annotated[Tenant, Depends(get_tenant)],
    retriever: Annotated[Retriever, Depends(get_retriever)],
    k: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[dict]:
    return [{"citation_id": h.citation_id, "doc_id": h.doc_id, "version": h.version, "section": h.section, "score": h.score, "text": h.text} for h in await retriever.search(q, tenant_id=tenant.id, k=k)]


@router.post("/threads/{thread_id}/memories", status_code=201)
async def extract_memories(
    thread_id: str,
    tenant: Annotated[Tenant, Depends(get_tenant)],
    user_id: Annotated[str, Depends(get_user_id)],
    store: Annotated[ThreadStore, Depends(get_store)],
    memory: Annotated[MemoryService, Depends(get_memory)],
    model: Annotated[ModelAdapter, Depends(get_model)],
) -> dict:
    """Run the extractor over this thread and consolidate into the user's memories. Records a memories_extracted event."""
    try:
        thread = await store.load(thread_id, tenant_id=tenant.id)
    except ThreadNotFound:
        raise NotFound(f"thread {thread_id} not found") from None
    try:
        outcomes = await memory.remember(tenant.id, user_id, thread, model)
    except ExtractionRejected as exc:
        raise InvalidRequest(str(exc)) from None
    persisted = len(thread.events)
    thread.append("memories_extracted", user_id=user_id, outcomes=[{"outcome": o, "memory_id": m.id, "content": m.content} for o, m in outcomes])
    await flush(store, thread, persisted)
    return {"user_id": user_id, "outcomes": [{"outcome": o, **m.as_dict()} for o, m in outcomes]}


@router.get("/memories")
async def list_memories(
    tenant: Annotated[Tenant, Depends(get_tenant)],
    user_id: Annotated[str, Depends(get_user_id)],
    memory: Annotated[MemoryService, Depends(get_memory)],
    include_history: bool = False,
) -> list[dict]:
    rows = await (memory.store.history(tenant.id, user_id) if include_history else memory.store.active_for(tenant.id, user_id))
    return [m.as_dict() | ({"deleted_reason": m.deleted_reason} if include_history else {}) for m in rows]


@router.delete("/memories/{memory_id}")
async def forget_memory(memory_id: str, tenant: Annotated[Tenant, Depends(get_tenant)], user_id: Annotated[str, Depends(get_user_id)], memory: Annotated[MemoryService, Depends(get_memory)]) -> dict:
    removed = await memory.forget(tenant.id, user_id, memory_id=memory_id, reason="user request via API")
    if not removed:
        raise NotFound(f"memory {memory_id} not found")
    return {"forgotten": [m.id for m in removed], "audit": memory_audit(removed)}


@router.delete("/memories")
async def forget_subject(subject: Annotated[str, Query(min_length=1)], tenant: Annotated[Tenant, Depends(get_tenant)], user_id: Annotated[str, Depends(get_user_id)], memory: Annotated[MemoryService, Depends(get_memory)]) -> dict:
    removed = await memory.forget(tenant.id, user_id, subject=subject, reason=f"user asked to forget subject {subject!r}")
    return {"forgotten": [m.id for m in removed], "audit": memory_audit(removed)}
