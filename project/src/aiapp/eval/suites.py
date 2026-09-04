"""Three suites, one shape: cases in, per-case pass/fail with a reason out, sliced by tag.

* tasks: end-to-end runs through run_agent with a scripted model; assertions are on the *trajectory*
  (which tools ran, whether a side effect waited for approval, what the final answer contains).
* tools: tool-selection accuracy (M3's harness as data).
* retrieval: Recall@k over the M4 golden set.
"""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from aiapp import FakeAdapter, ModelResponse, Thread, tool_call_response
from aiapp.knowledge import Retriever, parse_markdown
from aiapp.knowledge.memory_store import InMemoryKnowledgeStore
from aiapp.adapters.embeddings import HashingEmbedding
from aiapp.runtime import Budget, ContextBuilder, RunContext, SkillLoader, ToolRegistry, ToolRunner, run_agent
from aiapp.runtime.loop import REQUEST_HUMAN_INPUT_SPEC
from aiapp.runtime.turn import Delta
from aiapp.storage.memory import InMemoryKeyValueStore
from aiapp.tools.demo import DocStore

ROOT = Path(__file__).resolve().parents[4]
GOLDEN_DIR = ROOT / "project/eval/golden"
SKILLS_DIR = ROOT / "project/skills"
M4_DOCS = ROOT / "project/m4-rag-and-memory/docs-sample"
M4_GOLDEN = ROOT / "project/m4-rag-and-memory/golden/qa.jsonl"


@dataclass
class CaseResult:
    case_id: str
    passed: bool
    tags: tuple[str, ...]
    reason: str = ""


@dataclass
class SuiteResult:
    name: str
    results: list[CaseResult] = field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return sum(r.passed for r in self.results) / len(self.results) if self.results else 0.0

    def slices(self) -> dict[str, float]:
        by_tag: dict[str, list[bool]] = defaultdict(list)
        for r in self.results:
            for t in r.tags:
                by_tag[t].append(r.passed)
        return {t: sum(v) / len(v) for t, v in sorted(by_tag.items())}

    def failures(self) -> list[CaseResult]:
        return [r for r in self.results if not r.passed]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


# ---- tasks -----------------------------------------------------------------------------------------
def _script(steps: list[dict]) -> list[ModelResponse]:
    out = []
    for s in steps:
        if "tool" in s:
            out.append(tool_call_response(s["tool"], s.get("arguments", {}), call_id=s.get("id")))
        else:
            out.append(ModelResponse(content=s["say"]))
    return out


async def run_task_case(case: dict) -> CaseResult:
    docs = DocStore()
    registry = ToolRegistry()
    docs.register_into(registry)
    skills = SkillLoader(SKILLS_DIR).discover(registry.names())
    skills.register_into(registry)
    runner = ToolRunner(registry, InMemoryKeyValueStore(), retry_base_delay_s=0.001)
    thread = Thread()
    model = FakeAdapter(script=_script(case["script"]))
    ctx = RunContext(tenant_id="eval", thread_id=thread.thread_id, allowlist=frozenset(case.get("allowlist", registry.names())))
    context = ContextBuilder("You are a document workspace assistant.", skill_catalog=skills.catalog())
    events = []
    async for item in run_agent(thread, model, runner, ctx=ctx, budget=Budget(max_steps=case.get("max_steps", 6)), context=context, skills=skills, timeout_s=2.0, user_content=case["user"]):
        if not isinstance(item, Delta):
            events.append(item)
    if case.get("approve") is not None and thread.status() == "paused":
        pending = thread.events[-1].data
        thread.append("human_input", confirm_tool_call_id=pending["confirm_tool_call_id"], approved=case["approve"])
        async for item in run_agent(thread, model, runner, ctx=ctx, budget=Budget(max_steps=case.get("max_steps", 6)), context=context, skills=skills, timeout_s=2.0, user_content=None):
            if not isinstance(item, Delta):
                events.append(item)

    expect = case["expect"]
    tools_ran = [e.data["name"] for e in events if e.type == "tool_result" and not e.data.get("is_error")]
    problems = []
    if "tools_ran" in expect and tools_ran != expect["tools_ran"]:
        problems.append(f"tools ran {tools_ran} != {expect['tools_ran']}")
    if "forbidden_tools" in expect and (extra := set(tools_ran) & set(expect["forbidden_tools"])):
        problems.append(f"forbidden tools ran: {sorted(extra)}")
    if "paused_for" in expect:
        paused = [e for e in events if e.type == "human_input_requested"]
        if not paused or paused[0].data.get("tool") != expect["paused_for"]:
            problems.append(f"expected a pause for {expect['paused_for']}")
    if "final_status" in expect and thread.status() != expect["final_status"]:
        problems.append(f"status {thread.status()} != {expect['final_status']}")
    if "stop_reason" in expect:
        last = thread.events[-1]
        if last.data.get("reason") != expect["stop_reason"]:
            problems.append(f"stop reason {last.data.get('reason')!r} != {expect['stop_reason']!r}")
    if "deleted" in expect and docs.deleted != expect["deleted"]:
        problems.append(f"deleted {docs.deleted} != {expect['deleted']}")
    if "answer_contains" in expect:
        answer = next((e.data.get("answer", "") for e in reversed(events) if e.type == "run_finished"), "")
        if expect["answer_contains"].lower() not in answer.lower():
            problems.append(f"answer {answer!r} lacks {expect['answer_contains']!r}")
    if "max_steps_used" in expect and thread.steps() > expect["max_steps_used"]:
        problems.append(f"{thread.steps()} steps > {expect['max_steps_used']}")
    return CaseResult(case["id"], not problems, tuple(case.get("tags", [])), "; ".join(problems))


async def run_tasks() -> SuiteResult:
    suite = SuiteResult("tasks")
    for case in load_jsonl(GOLDEN_DIR / "tasks.jsonl"):
        suite.results.append(await run_task_case(case))
    return suite


# ---- tools -----------------------------------------------------------------------------------------
TOOL_ARGS = {"search_docs": {"query": "policy"}, "read_doc": {"doc_id": "doc_refunds"}, "delete_doc": {"doc_id": "doc_refunds"}, "load_skill": {"name": "expense-report"}, "request_human_input": {"question": "which?"}}


async def run_tools(model=None) -> SuiteResult:
    cases = load_jsonl(GOLDEN_DIR / "tools.jsonl")
    registry = ToolRegistry()
    DocStore().register_into(registry)
    skills = SkillLoader(SKILLS_DIR).discover(registry.names())
    skills.register_into(registry)
    specs = [*registry.specs(registry.names()), REQUEST_HUMAN_INPUT_SPEC]
    if model is None:
        model = FakeAdapter(script=[tool_call_response(c["expected"], TOOL_ARGS[c["expected"]]) if c["expected"] else ModelResponse(content="Sure.") for c in cases])
    context = ContextBuilder("You are a document workspace assistant. Use tools when they help; answer directly for small talk.", skill_catalog=skills.catalog())
    suite = SuiteResult("tools")
    for c in cases:
        thread = Thread()
        thread.append("user_message", content=c["user"])
        reply = await model.complete(context.build(thread), tools=specs)
        picked = reply.tool_calls[0].name if reply.tool_calls else None
        suite.results.append(CaseResult(c["id"], picked == c["expected"], tuple(c.get("tags", [])), "" if picked == c["expected"] else f"picked {picked!r}, expected {c['expected']!r}"))
    return suite


# ---- retrieval ---------------------------------------------------------------------------------------
async def run_retrieval(k: int = 5) -> SuiteResult:
    retriever = Retriever(InMemoryKnowledgeStore(), HashingEmbedding())
    for path in sorted(M4_DOCS.glob("*.md")):
        await retriever.ingest("eval", parse_markdown(path.stem, path.read_text(encoding="utf-8")))
    suite = SuiteResult("retrieval")
    for i, g in enumerate(load_jsonl(M4_GOLDEN)):
        hits = await retriever.search(g["q"], tenant_id="eval", k=k)
        ok = any(g["must_contain"] in h.text for h in hits)
        suite.results.append(CaseResult(f"q{i:02d}", ok, (g["doc_id"],), "" if ok else f"top-{k}: {[h.citation_id for h in hits[:3]]}"))
    return suite
