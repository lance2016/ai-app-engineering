"""Identity comes from the request, never from the model.

Multi-tenant agents read documents that belong to different customers. If the
tool takes `tenant_id` from the model's arguments, an injected or confused
model can read another tenant's data. The tenant must be bound by the runtime
from the authenticated request and enforced inside the tool.

Run:  uv run python lessons/20-security-governance/code/02_tenant_isolation.py
      INJECT_TRUST_MODEL_TENANT=1 uv run python lessons/20-security-governance/code/02_tenant_isolation.py
Expect: correctly bound, the cross-tenant read is denied. Trusting the model's
        tenant_id leaks tenant B's document to tenant A's session.
"""

# %% imports
import os
from dataclasses import dataclass

from aiapp import Message, ToolCall

INJECT_TRUST_MODEL_TENANT = os.environ.get("INJECT_TRUST_MODEL_TENANT") == "1"

DOCS = {
    ("tenant_a", "doc_1"): "Tenant A: Q3 roadmap",
    ("tenant_b", "doc_9"): "Tenant B: salary bands (confidential)",
}


# %% request_context
@dataclass(frozen=True)
class RequestContext:
    """Filled from the authenticated request. The model never sees or sets it."""

    tenant_id: str
    user_id: str
    role: str


# %% tool_with_authorization
def read_doc(ctx: RequestContext, call: ToolCall) -> Message:
    tenant = call.arguments.get("tenant_id", ctx.tenant_id) if INJECT_TRUST_MODEL_TENANT else ctx.tenant_id
    doc_id = call.arguments["doc_id"]
    content = DOCS.get((tenant, doc_id))
    if content is None:
        # Same answer for "does not exist" and "not yours": do not leak existence.
        return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"document {doc_id} not found")
    return Message(role="tool", tool_call_id=call.id, content=content)


# %% run
def main() -> None:
    ctx = RequestContext(tenant_id="tenant_a", user_id="u_1", role="viewer")
    own = ToolCall(id="c1", name="read_doc", arguments={"doc_id": "doc_1"})
    # The model (confused or injected) asks for another tenant's document by naming the tenant.
    cross = ToolCall(id="c2", name="read_doc", arguments={"doc_id": "doc_9", "tenant_id": "tenant_b"})
    for call in (own, cross):
        result = read_doc(ctx, call)
        print(f"{call.arguments} -> [{'ERROR' if result.is_error else 'ok'}] {result.content}")
    leaked = not read_doc(ctx, cross).is_error
    print("LEAK: tenant A read tenant B's data" if leaked else "isolation held")


if __name__ == "__main__":
    main()
