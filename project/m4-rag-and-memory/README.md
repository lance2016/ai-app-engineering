---
status: complete
kind: impl
depends_on: lessons/04, 13, 14, 15
---

# M4 Tiny-RAG 与 Memory

> 给 Agent 接上外部知识和跨会话记忆。RAG 用 pgvector 加 PostgreSQL 全文检索做混合检索，每个回答带能回链到原文位置的引用，而且引用会被代码校验；Memory 只存用户自己说过的事，每条带来源，可查可删，删了能证明。评测从第一天就在：31 条 golden 问答和 Recall@k 脚本，基线数字写在下面。

## 这一步加什么

- **M4.1 索引与检索**：`parse_markdown()` 加 `chunk_document()` 按标题切段、段内按段落凑到 `max_chars`，每个 chunk 是文档文本的一个连续切片（`start`/`end`），带 `content_hash`。`Retriever.ingest()` 只给哈希变了的 chunk 算 embedding，同一文档新版本整体替换旧版本。检索两路：pgvector 余弦距离和 `tsvector` 全文检索，用 RRF 融合。租户 id 是每条 SQL 的硬过滤；每个向量记录 `embedding_model`，不同模型的向量永不比较
- **Embedding 走 adapter**：`EmbeddingAdapter` 协议，`HashingEmbedding` 离线确定性（第 13 课 ragkit 的构造），`OpenAICompatibleEmbedding` 接 DashScope / OpenAI，`EMBEDDING_PROVIDER` 选。DeepSeek 没有 embedding 接口
- **M4.2 引用与评测**：`search_knowledge` 工具返回带 `citation_id`（`doc@v1#n`）的来源，system prompt 附加引用要求。运行结束后路由从本轮 `tool_result` 事件重建来源表，`verify_citations()` 检查每个引用是否真的检索到过、所支持的句子是否和来源有词面重叠，结果追加为 `citations_checked` 事件进线程。`golden/qa.jsonl` 31 条问答，`scripts/eval_recall.py` 算 Recall@1/3/5 并把每个 miss 分成 `not_indexed`（切块问题）和 `outside_top_k`（检索问题）
- **M4.3 Memory**：`extract_candidates()` 让模型输出结构化候选，每条必须带 `source_event_seqs` 且只能指向本线程的 `user_message`，否则整批拒绝。`MemoryService.remember()` 去重、同主题新的取代旧的（旧的留在历史里，不再展示）。`recall()` 按租户加用户过滤再排相关性；记忆少于 k 条时全部注入。`forget()` 是软删除，带原因，`history` 视图能看到删了什么、为什么、来源在哪
- **接进运行时**：每轮请求前按用户的这句话召回记忆，作为可缓存前缀之后的一段 `user` 消息注入（`ContextBuilder.memory_block`），`context` 报告多了 `memory_tokens`。工具处理器可以声明 `ctx` 参数拿到 `RunContext`，`search_knowledge` 靠它做租户过滤，模型参数里没有租户
- **API**：`POST /v1/documents` 灌文档返回 ingest 报告；`GET /v1/documents`；`DELETE /v1/documents/{doc_id}` 返回每个派生存储的残留计数；`GET /v1/knowledge/search?q=`；`POST /v1/threads/{id}/memories` 抽取并整合记忆，追加 `memories_extracted` 事件；`GET /v1/memories`（`include_history=true` 看审计视图）；`DELETE /v1/memories/{id}` 和 `DELETE /v1/memories?subject=` 返回审计。用户身份来自 `X-User-ID` 头，缺省等于租户
- **两套实现过同一套契约测试**：`InMemoryKnowledgeStore` + `InMemoryMemoryStore`，`PostgresKnowledgeStore` + `PostgresMemoryStore`。迁移 `0002` 建 `document`、`chunk`（`vector` 列加 GIN 索引的 `tsvector` 生成列）、`memory` 三张表

实际目录：

```text
project/src/aiapp/
├── adapters/embeddings.py       # EmbeddingAdapter, HashingEmbedding, OpenAICompatibleEmbedding, get_embedding_adapter()
├── knowledge/
│   ├── base.py                  # Document, Chunk, Hit（citation_id）, IngestReport, KnowledgeStore 协议
│   ├── ingest.py                # parse_markdown(), chunk_document(), content_hash(), quality_problems()
│   ├── hybrid.py                # rrf()
│   ├── citations.py             # verify_citations(), render_sources()
│   ├── retriever.py             # Retriever.ingest() / search()
│   ├── memory_store.py          # InMemoryKnowledgeStore（暴力余弦 + BM25）
│   ├── postgres_store.py        # PostgresKnowledgeStore（pgvector + tsvector）
│   ├── memory.py                # Memory, MemoryStore 协议, extract_candidates(), MemoryService, InMemoryMemoryStore
│   └── postgres_memory.py       # PostgresMemoryStore
├── tools/knowledge.py           # search_knowledge 工具；sources_from_tool_result()
├── storage/migrations/versions/0002_knowledge_and_memory.py
└── api/routes/knowledge.py      # /documents, /knowledge/search, /threads/{id}/memories, /memories
project/m4-rag-and-memory/
├── docs-sample/*.md             # 6 份示例文档
└── golden/qa.jsonl              # 31 条问答，带 doc_id 和 must_contain
scripts/eval_recall.py
tests/project/m4/
├── test_ingest.py               # 切片、标题边界、哈希稳定、质量检查
├── test_knowledge_store_contract.py   # 两种后端：检索、租户隔离、版本替换与向量复用、删除无残留、跨模型不比较、Recall 基线
├── test_citations.py
├── test_memory.py               # 两种后端：来源必填、去重与取代、按用户召回、可证明的遗忘
└── test_api_m4.py               # 文档进出、带引用回答与校验、记忆抽取→下一轮注入→遗忘
```

## 基线（2026-09-04，hashing embedding，max_chars=600）

| 检索器 | 内存后端 R@1 / R@3 / R@5 | PostgreSQL 后端 R@1 / R@3 / R@5 |
|---|---|---|
| text（BM25 / tsvector） | 0.74 / 0.87 / 0.90 | 0.71 / 0.84 / 0.90 |
| vector（hashing） | 0.42 / 0.74 / 0.81 | 0.45 / 0.74 / 0.84 |
| hybrid（RRF） | 0.65 / 0.84 / 0.90 | 0.65 / 0.84 / 0.87 |

两个后端的差别来自打分函数：内存实现是 BM25，PostgreSQL 是 `ts_rank`，向量路径的排序也受浮点精度影响。内存后端的三个 miss 都是 `outside_top_k`：问句和原文没有共同词面（"看到退款"对"paid back"，"2FA"对"Two-factor"）。这正是 hashing 向量的边界，换真实 embedding 模型后重跑 `EMBEDDING_PROVIDER=dashscope uv run python scripts/eval_recall.py` 把新数字补到这里。切块大小在这套语料上不改变结果，因为每个小节只有一段，chunk 从不跨标题；语料换成长文档后 `--max-chars` 才会体现差别。测试里的门禁是 hybrid Recall@5 ≥ 0.85。

## 运行步骤

```bash
uv run pytest tests/project/m4 -q                       # 内存后端；Postgres 可达时两种后端都跑
uv run python scripts/eval_recall.py                    # 上面那张表
uv run python scripts/eval_recall.py --max-chars 200 --k 3

docker compose up -d --wait
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp REDIS_URL=redis://localhost:6379/0
uv run alembic -c project/src/aiapp/storage/alembic.ini upgrade head
uv run python scripts/eval_recall.py --postgres
uv run uvicorn aiapp.api.app:create_app --factory
for f in project/m4-rag-and-memory/docs-sample/*.md; do
  curl -s -X POST localhost:8000/v1/documents -H "Authorization: Bearer dev-token" -H "Content-Type: application/json" \
       -d "$(python3 -c "import json,sys;print(json.dumps({'doc_id': sys.argv[1], 'text': open(sys.argv[2]).read()}))" $(basename $f .md) $f)"; echo; done
curl -s "localhost:8000/v1/knowledge/search?q=dispatch+cutoff" -H "Authorization: Bearer dev-token"
curl -s -X DELETE localhost:8000/v1/documents/warranty -H "Authorization: Bearer dev-token"   # 看 residue 全零
# 记忆：X-User-ID 区分同一租户下的用户
curl -s -X POST localhost:8000/v1/threads/<id>/memories -H "Authorization: Bearer dev-token" -H "X-User-ID: u42"
curl -s "localhost:8000/v1/memories?include_history=true" -H "Authorization: Bearer dev-token" -H "X-User-ID: u42"
```

fake 模型不会自己调 `search_knowledge` 或输出记忆 JSON，所以走 HTTP 看完整流程要用 `MODEL_PROVIDER=deepseek`；离线看流程用 `tests/project/m4/test_api_m4.py` 里的剧本。

## 验收证据

- [x] `eval_recall.py` 输出 Recall@5 和每条失败用例的分类，基线数字写在本 README（`test_recall_at_5_on_the_golden_set_meets_the_baseline` 守住 0.85）
- [x] 换切块策略再跑一次，Recall 变化有记录：这套语料上 `--max-chars 200` 和 600 结果相同，原因写在上面
- [x] 回答里的每个引用都能通过 `doc_id + version + span` 定位到原文，测试断言 chunk 文本确实等于 `document.text[start:end]`（`test_every_chunk_is_a_slice_of_the_document_and_stays_inside_one_section`）；引用校验通过与编造引用被抓，HTTP 两层都有测试
- [x] 失败注入：文档更新到新版本后旧版本的 chunk 不再被召回，引用显示新版本号，只有变了的段落重新算 embedding（`test_new_version_replaces_old_chunks_and_reuses_unchanged_vectors`）
- [x] 删除演练：删除一个文档后每个派生存储残留为零、检索不到；删除一条记忆后下一轮上下文里确实没有它，历史视图有删除原因（`test_delete_leaves_no_residue_anywhere`、`test_forget_is_targeted_and_leaves_an_audit_trail`、`test_memories_are_extracted_recalled_next_turn_and_forgotten`）
- [x] 租户 A 的查询永远召回不到租户 B 的 chunk，另一个用户的记忆永远不出现（`test_tenants_never_see_each_other`、`test_recall_is_per_user_and_relevance_ranked`）
- [x] 不同 embedding 模型的向量永不比较（`test_vectors_from_another_model_are_never_compared`），这是第 04 课那个"换模型忘了重建"事故的代码级防线
- [ ] 真实 embedding 模型的 Recall 基线：需要 DashScope 或 OpenAI key，跑完把数字补进上表

## 依赖的课程

lessons/04, 13, 14, 15

---

[← M3](../m3-tool-workflow/README.md) · [项目总览](../README.md) · [M5 →](../m5-production/README.md)
