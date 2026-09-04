"""An Architecture Decision Record as data, rendered to Markdown.

Following Michael Nygard's format: context, decision, status, consequences,
plus two fields this course insists on: the alternatives that were rejected
and the exit criteria that would make you revisit the decision.

Run:  uv run python lessons/23-system-design-decisions/code/02_adr.py
Expect: a complete ADR printed as Markdown for "tenant knowledge: RAG vs fine-tune".
"""

# %% imports
from dataclasses import dataclass, field
from datetime import date


# %% model
@dataclass(frozen=True)
class Option:
    name: str
    pros: list[str]
    cons: list[str]


@dataclass(frozen=True)
class ADR:
    number: int
    title: str
    status: str  # proposed | accepted | superseded
    context: str
    options: list[Option]
    decision: str
    consequences: list[str]
    exit_criteria: list[str]  # observations that should reopen this decision
    decided_on: date = field(default_factory=date.today)

    def to_markdown(self) -> str:
        lines = [f"# ADR-{self.number:03d}: {self.title}", "", f"- Status: {self.status}", f"- Date: {self.decided_on.isoformat()}", "", "## Context", "", self.context, "", "## Options considered", ""]
        for o in self.options:
            lines += [f"### {o.name}", ""]
            lines += [f"- (+) {p}" for p in o.pros]
            lines += [f"- (-) {c}" for c in o.cons]
            lines.append("")
        lines += ["## Decision", "", self.decision, "", "## Consequences", ""]
        lines += [f"- {c}" for c in self.consequences]
        lines += ["", "## Exit criteria (revisit if any becomes true)", ""]
        lines += [f"- {e}" for e in self.exit_criteria]
        return "\n".join(lines)


# %% example
EXAMPLE = ADR(
    number=7,
    title="Per-tenant knowledge: retrieval over fine-tuning",
    status="accepted",
    context=(
        "Each tenant uploads 200-5000 documents that change weekly and must be deletable within 24h "
        "for compliance. Answers must cite sources. The team has two engineers and no GPU budget."
    ),
    options=[
        Option("Fine-tune one model per tenant", ["Fast inference, no retrieval hop"],
               ["Weekly retraining per tenant", "Cannot delete a fact on request", "No citations", "GPU cost"]),
        Option("Shared model + per-tenant RAG index", ["Delete = remove chunks", "Citations for free", "One model to operate"],
               ["Retrieval quality caps answer quality", "Extra latency and tokens per turn"]),
        Option("Long context: stuff all docs into the prompt", ["Simplest code"],
               ["Cost scales with corpus", "Does not fit above ~1k docs", "No source attribution"]),
    ],
    decision="Shared model with a per-tenant RAG index (pgvector + BM25), tenant id as a hard filter on every query.",
    consequences=[
        "Need an ingestion pipeline with document versions and deletion (lesson 15).",
        "Need Recall@k on a per-tenant golden set before launch (lesson 17).",
        "Answer latency budget grows by one retrieval hop (~150ms p95).",
    ],
    exit_criteria=[
        "A tenant needs style/behaviour changes that retrieval cannot express.",
        "Retrieval recall stays below 0.8 after two rounds of chunking/reranking work.",
        "Per-turn token cost from retrieved context exceeds 40% of the bill.",
    ],
)


# %% run
if __name__ == "__main__":
    print(EXAMPLE.to_markdown())
