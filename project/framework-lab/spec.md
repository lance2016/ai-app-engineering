# Framework Lab｜共同规格

这份规格固定“要解决的问题”，不固定框架的实现方式。四个适配位是同一个 baseline、LangGraph、OpenAI Agents SDK、Claude Agent SDK；任何框架原生能力都要翻译成 `labkit.protocol.LabRuntime` 后再比较。

## 任务

实现一个审批型文档 Agent：

1. 用户询问文档时，可以调用 `search_docs` 和 `read_doc`，完成后返回答案。
2. 用户要求删除文档时，模型只能提出 `delete_doc`；运行时必须暂停并请求批准，批准后才执行。
3. 用户问题不完整时，Agent 可以调用 `request_human_input`，收到答案后从 checkpoint 继续。
4. 进程在暂停或任意已记录步骤后退出，新进程必须从同一 thread 恢复；已经完成的副作用不能重跑。
5. 暂停期间收到新消息必须拒绝，不得偷偷覆盖 pending input。
6. 未知工具、超出步数、工具错误和供应商错误必须成为可观察的失败或工具结果，不能让进程无提示崩溃。

共同假设：fake model 按剧本返回；文档系统在测试中提供两个只读工具和一个可删除文档；持久化目录是进程外部的 durable world。实现可以用文件、SQLite、框架 session 或其他存储，但必须在 README 里说清楚恢复语义。

## 事件与状态契约

适配器把框架原生事件归一化为这些事件类型：`user_message`、`run_started`、`assistant_message`、`tool_result`、`human_input_requested`、`human_input`、`run_finished`、`run_failed`。原生事件里没有对应物时，不虚构细节；在 `RunOutcome.detail` 说明丢失了什么。

每次调用返回一个 `RunOutcome`：

| 状态 | 必须满足 |
|---|---|
| `finished` | 有最终答案和 `run_finished`，副作用已按契约完成 |
| `paused` | 有 pending 类型和参数，副作用尚未执行，状态可跨进程恢复 |
| `rejected` | thread 正在等待输入，新消息没有改动事件或外部系统 |
| `failed` | 有可诊断的 detail，步数或供应商异常不会无限重试 |

## 一致性场景与验收

`labkit/scenarios.py` 的八个场景是行为门槛：

| 场景 | 证明的能力 | 当前测试 |
|---|---|---|
| read-only happy path | 工具往返和最终回答 | 自动化 |
| confirmation pause / restart / resume | HITL、checkpoint、幂等 | 自动化 |
| confirmation declined | 拒绝是可处理结果 | 自动化 |
| question round trip | 人工回答后继续 | 自动化 |
| double texting | pending 状态的并发策略 | 自动化 |
| history survives restart | durable history | 自动化 |
| step limit | 运行时拥有停止条件 | 自动化 |
| unknown tool | allowlist / 错误回喂 | 自动化 |

命令：`uv run pytest tests/project/framework_lab -q`。实现缺少某个框架原语时可以 `NotSupported`，但必须在 [scorecard.md](./scorecard.md) 写明代价和替代实现，不得静默跳过。

## 自动测试与阅读评分的边界

一致性测试只判断跨框架都能观察到的行为。MCP 原生支持、OpenTelemetry 接入、部署形态、调试体验和 lock-in 不强行压成一个断言，统一放入评分卡，附代码行或官方文档证据。这样不会因为“都能返回最终答案”就掩盖生产差异。

## 比较规则

- 每个实现必须提供 `agent.py`、`adapter.py` 和 README；fake replay 不调用网络。
- 先记录框架原生语义，再记录归一化层的损耗；不要把 baseline 的便利误写成框架能力。
- 每个评分格用 0–2 三档证据：0 = 缺失或不可控，1 = 可实现但要自建，2 = 原生且可验证。
- 不打总分，不做“最好框架”排名。选型结论必须引用需求约束、测试结果、评分卡和 lock-in 后果。
