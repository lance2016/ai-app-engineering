# TODO

> 维护者的待办清单，按优先级排。做完一项就删掉，动手前先读 [AGENTS.md](./AGENTS.md)。
> 截至 2026-09-04：课程内容与 M1～M5 已完成；本轮已完成 README / Stage onboarding、课程模板回填、Framework Lab 规格与评分卡、Production Agent Service Capstone 样板。阶段 4 的两个 SDK 适配器仍在进行中。

## 阶段 4：Framework Lab（进行中）

已有：`project/framework-lab/labkit/`（`LabRuntime` 协议、8 个一致性场景）、`baseline/`（M3 运行时的适配）、`langgraph_impl/`（图 + interrupt + SQLite checkpoint），两者 8/8 场景通过（`uv run pytest tests/project/framework_lab`）。框架依赖在 `frameworks` 依赖组：`uv sync --group frameworks`。

- [ ] `openai_agents_impl/`：`agents.models.interface.Model` 的 fake 回放剧本；`function_tool(needs_approval=True)` 做确认门，`result.to_state()` / `RunState.from_string()` 持久化到 workdir 实现跨进程续跑；`request_human_input` 用 `StopAtTools` 结束本轮、下一轮以用户回答继续；`SQLiteSession` 存历史；`MaxTurnsExceeded` → failed。已确认 0.22.0 有这些 API
- [ ] `claude_agent_sdk_impl/`：`ClaudeSDKClient(options, transport=FakeTransport)` 伪造 CLI 传输层。伪 CLI 要处理 `control_request initialize`、发 `assistant`（含 `tool_use`）、对副作用工具发 `control_request can_use_tool` 并读 `control_response`、发 `user` 的 `tool_result`、以 `result` 结束（必填字段见 `_internal/message_parser.py` 的 `case "result"`）。跨进程确认：Deny 并记 pending，`resume=session_id` 续跑时 Allow。会话持久化由伪 CLI 写 workdir。注意 `claude_agent_sdk/types.py` 会遮蔽标准库 `types`，不要在该包目录下运行 Python
- [x] `spec.md`：正式共同规格、事件契约、8 个一致性场景，以及自动测试 / 阅读评分边界
- [x] `scorecard.md`：12 维 × 4 实现的证据表，不排名；末尾一张选型工作表
- [ ] 每个实现目录的 README：概念映射表、顺手处、别扭处、锁定点。LangGraph 已知的两个发现要写进去：节点内 interrupt 之前的副作用在 resume 时会重跑；`recursion_limit` 是步数上限的唯一原语
- [x] Lab 总览 README 的现有目录名已改为可导入的 `baseline/ langgraph_impl/`，状态保持 draft；两个 SDK 目录待实现后再添加
- [x] 给 05～14 课补「框架映射」小节（一张表，三个框架）
- [x] CI 已用 `uv sync --all-groups` 安装框架依赖，并由全量 `pytest` 跑 `tests/project/framework_lab`

## 阶段 5：Capstone

- [x] Capstone 1 `Production Agent Service`：补齐约束、架构、自动化验收、eval、trace、reliability、security、cost、deployment、runbook、ADR、demo 和七维三档 rubric
- [ ] 其他三个 Capstone 保持 outline，等各自实现前再补约束、评分量表和自动化验收
- [ ] `tests/capstones/durable/`：Capstone 3 的 kill 与恢复 harness（可复用 `labkit.scenarios.confirmation_pause_restart_resume` 的思路）
- [ ] Capstone 1 的学生实现补 M5 没做的：PII 出站过滤（第 20 课 `03`）、Skill 内容哈希钉版本（第 20 课 `04`）

## 阶段 6：前置新内容

- [ ] `prerequisites/algorithms/` A00～A06 从 outline 写到 complete，每篇 2～3 个 `code/` 文件
- [ ] `prerequisites/backend/04-redis` 正文与代码
- [ ] `prerequisites/llm-foundations/` F02、F07 正文；F00～F06 补 `exercises.md`

## 阶段 7：模板回填与审计

- [x] 24 课补「为什么需要」「生产方案」「框架映射」，并统一阅读 / 实战模式提示
- [ ] `check_lesson_template.py --strict` 转为 CI 门禁，做一次状态审计

## 阶段 8：开源产品化的下一步

- [x] 首屏、Stage 0–7 入口、Quick Start、主项目 Hero Demo 和 cross-platform onboarding
- [x] 关键课程补正常 / 失败、状态变化、数据流或决策回路图
- [x] `.github/assets/demo/` 和 `reference/demo-recording.md` 建立真实素材录制规范
- [ ] 录制并提交四个真实 Demo 媒体；没有完成前不要在 README 宣称已有截图 / GIF
- [ ] 为 `tests/capstones/production_agent_service/` 补一组独立于 M1–M5 的 Capstone 验收测试
- [ ] 评估是否需要 MkDocs / docs site；在不新增主线课程前先观察 README + GitHub rendering 的反馈

## 需要真实 key 才能补的数字

- [ ] `MODEL_PROVIDER=deepseek uv run pytest tests/project/m3/test_tool_accuracy.py -s`：工具选型准确率真实基线，写回 M3 README
- [ ] `EMBEDDING_PROVIDER=dashscope uv run python scripts/eval_recall.py`：真实 embedding 的 Recall，写回 M4 README
- [ ] `MODEL_PROVIDER=deepseek uv run python scripts/eval_run.py --real-tools`（加 `REAL_JUDGE=1`）：写回 `project/eval/baseline.json` 和 M5 README
- [ ] M1 验收里"客户端断开后流被取消"一条要用真实模型手工验证

## 已知的小债

- 第 00、04、23 课的 `code/` 没有 `INJECT_` 开关（模板检查里是警告）；这是示例层债务，不影响已完成的正文模板回填
- `chunk.embedding` 是无维度的 `vector` 列，没有 HNSW 索引；embedding 模型定下来后加一次迁移
- `templates/lesson-README.md` 里的占位链接被 `check_links.py` 跳过（整个 `templates/` 目录不检查）
