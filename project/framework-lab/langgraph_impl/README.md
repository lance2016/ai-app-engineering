# LangGraph｜显式 StateGraph

LangGraph 把审批型 Agent 表达成 `agent → tools → agent` 的 StateGraph，用 `interrupt()` 暂停，用 `Command(resume=...)` 继续，用 `AsyncSqliteSaver` 保存 checkpoint。适配器把这些原生对象翻译成 Lab 的事件和状态。

## 概念映射

| Lab 概念 | LangGraph 的位置 | 证据 |
|---|---|---|
| Control Flow | `StateGraph`、条件边、`recursion_limit` | [`agent.py`](./agent.py) |
| State | `AgentState.messages` + `steps` | [`agent.py#L22`](./agent.py#L22) |
| Checkpoint | `AsyncSqliteSaver`，按 `thread_id` | [`adapter.py#L39`](./adapter.py#L39) |
| HITL | `interrupt()` / `Command(resume=...)` | [`agent.py#L70`](./agent.py#L70) |
| Tool | tools node + `ToolRegistry` | [`agent.py#L47`](./agent.py#L47) |
| Context | message state 由节点重新解释 | 需要额外的 ContextBuilder 才能完全控制 |

## 顺手与别扭

- **顺手**：节点、边和中断让流程图可读；checkpoint 和跨进程 resume 已进入同一套执行模型；`recursion_limit` 能阻止无限循环。
- **别扭**：节点内 `interrupt()` 之前发生的副作用，在 resume 时可能重新执行；副作用必须移到可幂等的工具层，不能放在节点前半段。
- **别扭**：`recursion_limit` 是图层的步数上限，不等于 token、美元或业务时间预算；这些预算仍要由应用 runtime 管。
- **锁定点**：`StateGraph`、`AIMessage`、`ToolMessage` 和 `Command` 会渗透到适配层；业务代码若直接保存它们，迁移成本会快速上升。

## 失败行为、观测与部署

图递归超限被适配器转换成 `failed`；pending interrupt 时新消息被拒绝；工具错误由 tool message 传回图。事件归一化本身只保留 Lab 契约，OpenTelemetry、MCP、租户权限和幂等仍需要应用层补上。

部署需要 LangGraph、SQLite checkpoint（或替换成生产 saver）和普通 Python 服务。它更适合必须把 durable execution、人工介入和分支流程作为一等概念的团队；不应因为有图就把固定 workflow 改造成 Agent。

运行：`uv sync --group frameworks` 后执行 `uv run pytest tests/project/framework_lab -q`。共同规格和评分口径见 [`../spec.md`](../spec.md) 与 [`../scorecard.md`](../scorecard.md)。
