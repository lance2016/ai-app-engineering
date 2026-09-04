---
status: complete
kind: impl
depends_on: lessons/05, 06, 07, 08, 09, 11, 12；可选 10
---

# M3 Tool Workflow

> 把第 05 课的守卫、第 06 课的循环与预算、第 07 课的暂停恢复、第 08 课的上下文组装合成一个运行时，接到 M2 的存储上，再从外部接入一个 MCP Server 和一个 Skill。这一步做完，服务是一个能干活、能停、能续、能被审计的 Agent。

## 这一步加什么

分四个子阶段，全部落在 `aiapp/runtime/`：

- **M3.1 Tool contract**：`ToolRegistry` 管"有什么工具"，请求级 allowlist 管"这次能看到什么"，`Tool.validate()` 用 Pydantic 模型或 JSON Schema 校验参数。`ToolRunner.run()` 按固定顺序过六道守卫：名字、白名单、参数、确认、幂等、执行。每个失败都是一条 `is_error=True` 的工具结果回喂给模型，不是异常。每次执行记一条带 `duration_ms`、`attempts`、`route` 的 `tool_result` 事件，这是最小 trace
- **M3.2 确认与幂等**：`has_side_effects=True` 的工具没有人批准就不跑。运行时追加 `human_input_requested(kind="confirmation", confirm_tool_call_id=…)` 并暂停；人的决定是一条 `human_input(confirm_tool_call_id, approved)` 事件，`approved=False` 变成"user declined"的错误结果让模型体面收尾。幂等键从租户、线程、调用 id 和规范化参数派生，经 `KeyValueStore.claim()` 认领；执行完记录结果，重试直接重放。失败路由照第 06 课：`TransientToolError` 带退避重试两次，`ValueError` 回喂，`ToolFailed` 记录并重放，工具崩溃释放键让修好的工具能重跑。同一个调用重复出现先警告一次再以 `off_track` 结束
- **M3.3 MCP 与 Skill**：`MCPToolSource` 起一个 stdio MCP Server，`tools/list` 的每个工具注册成普通 `Tool`，`annotations.readOnlyHint` 决定要不要确认。服务器死了算瞬时错误，处理器重连一次交给 runner 的重试；一直死就是错误结果，不是 500。`SkillLoader` 三级加载：目录进 system prompt，`load_skill` 和 `read_skill_reference` 是两个只读工具，加载成功追加 `skill_loaded(name, tokens)` 事件。安装前校验 frontmatter、slug、描述长度、allowed-tools
- **M3.4 Handoff**：没做。理由记在下面"选型记录"
- **上下文组装** `ContextBuilder`：system prompt 加 Skill 目录放最前（可缓存），历史按整轮从最早开始裁到预算内，超过 4000 字符的工具结果只给模型看头尾，线程保留全文。每条 `assistant_message` 事件带一份 `context` 报告：各段 token、裁掉多少、整形多少
- **API**：`POST /v1/threads/{id}/messages` 换成 `run_agent`，请求体可带 `allowed_tools` 缩小但不能放大服务端白名单；新增 `POST /v1/threads/{id}/human-input` 回答问题或批准副作用并从断点续跑；线程处于 `paused` 时发新消息返回 409
- **演示工具**：`aiapp/tools/demo.py` 一个文档工作区，`search_docs`、`read_doc` 只读，`delete_doc` 有副作用，`fail_next_searches` 注入瞬时故障
- **Skill**：`project/skills/expense-report/`，从第 12 课的示例改来，`allowed-tools` 改成本项目的工具名
- **测试** `tests/project/m3/`：31 个用例，加一个 20 条用例的工具选型准确率脚手架

实际目录：

```text
project/src/aiapp/
├── runtime/
│   ├── registry.py     # Tool, ToolRegistry, signature()；Pydantic 或 JSON Schema 校验
│   ├── runner.py       # ToolRunner.run(): validate → authorize → confirm → idempotency → execute → trace；RunContext, NeedsConfirmation, ToolOutcome
│   ├── loop.py         # run_agent(): settle pending → build context → stream model → charge budget → stop conditions → off-track
│   ├── budget.py       # Budget（步数 / token / 时间）, StopReason
│   ├── context.py      # ContextBuilder：稳定前缀、整轮裁剪、工具结果整形、context 报告
│   ├── skills.py       # SkillLoader：discover / catalog / load / reference / register_into；validate_skill()
│   ├── mcp_source.py   # MCPToolSource：tools/list → Tool；断连重连；isError → ToolFailed
│   ├── errors.py       # TransientToolError, ToolFailed
│   └── turn.py         # Delta；run_turn 现在是 run_agent 的无工具包装
├── mcp/
│   ├── client.py       # StdioMcpClient：JSON-RPC over stdio，initialize 生命周期
│   └── toy_notes_server.py   # 测试和演示用的 MCP Server，带 readOnlyHint，可 --read-only / --crash-on
├── tools/demo.py       # DocStore：search_docs, read_doc, delete_doc
└── api/routes/threads.py     # /messages 用 run_agent；/human-input 续跑；allowed_tools
project/skills/expense-report/{SKILL.md, references/policy.md}
project/m3-tool-workflow/code/01_agent_with_tools_offline.py
tests/project/m3/
├── test_runner.py          # 六道守卫各一个用例，加重放、崩溃、trace
├── test_loop.py            # 停止条件、暂停恢复、问人、跑偏、超时、Skill、上下文
├── test_mcp.py             # 只读注册、副作用确认、往返、重连、持续崩溃
├── test_api_m3.py          # SSE 工具事件、确认与提问的 HTTP 往返、allowed_tools
└── test_tool_accuracy.py   # 20 条"用户说 X 该调 Y"
```

## 选型记录：为什么是 Workflow 不是自治 Agent，为什么没做 Handoff

按第 09 课的分类，M3 是一条"校验、确认、执行"的确定性链加一个由模型决定下一步的循环，每一步的守卫和停止条件都在代码里。没有让模型自由规划，因为每个副作用都要过确认门，路径可枚举。M3.4 的 router + worker 拆分没做：当前工具集只有五个，一个 Agent 的上下文装得下，拆成两个只会多一处交接丢信息的地方。等 M4 接上检索、工具集和上下文都变大时再评估，评估标准是第 10 课的三个问题。Framework Lab 里三个框架的实现都会做 handoff 版本作对照。

## 运行步骤

```bash
uv run pytest tests/project/m3 -q                                   # 31 passed，离线
uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
INJECT_FLAKY_SEARCH=1 uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
USER_DECISION=no uv run python project/m3-tool-workflow/code/01_agent_with_tools_offline.py
uv run pytest tests/project/m3/test_tool_accuracy.py -s             # 准确率表；MODEL_PROVIDER=deepseek 测真实模型

# 起服务，接一个只读的 MCP Server
docker compose up -d --wait
export DATABASE_URL=postgresql+asyncpg://aiapp:aiapp@localhost:5432/aiapp REDIS_URL=redis://localhost:6379/0
AIAPP_MCP_COMMAND="uv run python -m aiapp.mcp.toy_notes_server --read-only" \
  uv run uvicorn aiapp.api.app:create_app --factory
# 发消息时用 allowed_tools 缩小工具范围
curl -N -X POST localhost:8000/v1/threads/<id>/messages -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{"content": "find the returns draft and delete it", "allowed_tools": ["search_docs", "delete_doc"]}'
# 流的最后一条是 human_input_requested(kind=confirmation)，用它的 confirm_tool_call_id 批准
curl -N -X POST localhost:8000/v1/threads/<id>/human-input -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" -d '{"confirm_tool_call_id": "<id>", "approved": true}'
```

fake 模型不会自己决定调工具，所以走 HTTP 看完整的工具流程要用 `MODEL_PROVIDER=deepseek`；离线看流程用上面的演示脚本和测试。

## 验收证据

- [x] `tests/project/m3` 覆盖七种路径各至少一个测试：未知工具、非法参数、白名单外、需确认、幂等重放、瞬时错误重试、跑偏升级（`test_runner.py`、`test_loop.py`）
- [x] 工具准确率测试：20 条"用户说 X 应该调用 Y"用例，fake 模型 100%（`test_tool_accuracy.py`）。真实模型的基线还没跑，M5 评测门禁接手时补
- [x] 失败注入：工具执行后、记录结果前进程死掉，恢复后同一幂等键不产生第二次副作用（`test_crash_between_execute_and_record_never_re_executes`，用残留的 `running` 键模拟）；同一调用重试直接重放（`test_side_effect_needs_confirmation_then_runs_once`）
- [x] MCP Server 断开时工具调用返回 `is_error` 结果而不是 500；中途死掉一次会被透明重连（`test_mcp.py` 最后两个用例）
- [x] Skill 只在触发条件满足时被加载，目录在 system prompt 里，正文不在；trace 里有 `skill_loaded` 事件和注入的 token 数（`test_skill_is_loaded_on_demand_and_traced`）
- [x] 每一步都有 trace 事件，能从事件线程重建"这次运行调了哪些工具、各花了多久、走了哪条路"（每条 `tool_result` 带 `name`、`duration_ms`、`attempts`、`route`；`run_finished` / `run_failed` 带 budget 快照）
- [x] 副作用不在模型的一句话上执行：暂停、批准、执行一次、拒绝后模型体面收尾，HTTP 和循环两层都有测试
- [x] 上下文按整轮裁剪且工具结果整形，线程保留全文（`test_context_drops_oldest_turns_and_shapes_big_tool_results`）
- [ ] 真实模型下的工具准确率基线数字：需要 key，`MODEL_PROVIDER=deepseek uv run pytest tests/project/m3/test_tool_accuracy.py -s`，把数字写回这里

## 依赖的课程

lessons/05, 06, 07, 08, 09, 11, 12；可选 10

---

[← M2](../m2-state-and-storage/README.md) · [项目总览](../README.md) · [M4 →](../m4-rag-and-memory/README.md)
