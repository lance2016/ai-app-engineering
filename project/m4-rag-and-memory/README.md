---
status: draft
kind: impl
depends_on: lessons/04, 13, 14, 15
---

# M4 Tiny-RAG 与 Memory

> 给 Agent 接上外部知识和跨会话记忆。RAG 用 pgvector 加 BM25 混合检索，每个回答带可回链的引用；Memory 只存用户偏好和已确认的事实，每条带来源，可查可删。评测从第一天就在：一个小 Golden set 和 Recall@k。

## 这一步加什么

- **M4.1 索引与检索**：解析（先只支持 Markdown 和纯文本）、切块（按标题层级加固定长度兜底）、embedding 写入 pgvector、BM25 用 PostgreSQL 全文检索；混合检索用 RRF 融合；租户 id 是每次查询的硬过滤
- **M4.2 引用与评测**：chunk 带 `doc_id`、`version`、`start`、`end`，回答里的引用能定位到原文位置；`golden/` 目录放 30 条问答加期望命中的 chunk；`Recall@k` 脚本；失败分类（没召回、召回了没用、用了但答错）
- **M4.3 Memory**：`MemoryExtractor` 在会话结束时用模型抽取候选记忆；`MemoryStore` 存记忆加来源事件 id；检索时按用户加租户过滤；删除演练：删除一条记忆后，下一轮上下文里确实没有它

目标目录：

```text
project/src/aiapp/knowledge/
├── ingest.py      # parse(path) -> Document; chunk(doc) -> list[Chunk]; index(chunks, tenant_id)
├── retriever.py   # Retriever.search(query, *, tenant_id, k, filters) -> list[Hit]
├── hybrid.py      # rrf(vector_hits, bm25_hits) -> list[Hit]
├── citations.py   # Hit -> Citation(doc_id, version, span)
└── memory.py      # MemoryExtractor, MemoryStore
golden/
└── tenant-demo/qa.jsonl
scripts/
└── eval_recall.py
```

关键接口：

```python
@dataclass(frozen=True)
class Hit:
    chunk_id: str; doc_id: str; version: int; text: str; score: float; span: tuple[int, int]

class Retriever(Protocol):
    async def search(self, query: str, *, tenant_id: str, k: int = 8, filters: dict | None = None) -> list[Hit]: ...

class MemoryStore(Protocol):
    async def add(self, tenant_id: str, user_id: str, text: str, *, source_event_id: int) -> Memory: ...
    async def search(self, tenant_id: str, user_id: str, query: str, k: int = 5) -> list[Memory]: ...
    async def delete(self, memory_id: str) -> None: ...
```

Embedding 通过 adapter 层调用，和聊天模型一样可替换；离线测试用第 04 课的确定性玩具 embedding。

## 运行步骤

```bash
docker compose up -d postgres redis      # postgres 镜像需带 pgvector
uv run alembic upgrade head
uv run python -m aiapp.knowledge.ingest --tenant tenant-demo ./docs-sample/
uv run python scripts/eval_recall.py --tenant tenant-demo --k 5
uv run pytest tests/knowledge
```

## 验收证据

- [ ] `eval_recall.py` 输出 Recall@5 和每条失败用例的分类，基线数字写进本 README
- [ ] 换切块策略（只按长度 vs 按标题）再跑一次，Recall 变化有记录
- [ ] 回答里的每个引用都能通过 `doc_id + version + span` 定位到原文，测试断言引用文本确实出自该位置
- [ ] 失败注入：把一个文档更新到新版本，旧版本的 chunk 不再被召回，引用显示新版本号
- [ ] 删除演练：删除一个文档和一条记忆，各自在下一次检索和下一轮对话中都不出现
- [ ] 租户 A 的查询永远召回不到租户 B 的 chunk，有专门的测试

## 依赖的课程

lessons/04, 13, 14, 15

---

[← 项目总览](../README.md)
