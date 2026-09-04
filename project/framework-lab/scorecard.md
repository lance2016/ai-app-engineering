# Framework Lab｜12 维评分卡

这张表不是排行榜。每格只回答“在共同规格下，团队需要付出多少控制权和实现成本”，并给出代码或测试证据。`0 / 1 / 2` 的定义见 [spec.md](./spec.md)。OpenAI Agents SDK 和 Claude Agent SDK 适配器尚未提交，先保留空格，不把计划写成结果。

| 维度 | Baseline | LangGraph | OpenAI Agents SDK | Claude Agent SDK |
|---|---|---|---|---|
| Control Flow | [显式 loop](./baseline/adapter.py#L39)；2 | [StateGraph](./langgraph_impl/agent.py#L29)；2 | 待实现；— | 待实现；— |
| State | [Thread event log](./baseline/adapter.py#L28)；2 | [AgentState](./langgraph_impl/agent.py#L22)；2 | 待实现；— | 待实现；— |
| Checkpoint | [per-step JSON](./baseline/adapter.py#L58)；1 | [AsyncSqliteSaver](./langgraph_impl/adapter.py#L39)；2 | 待实现；— | 待实现；— |
| Human-in-the-loop | [pending event](./baseline/adapter.py#L67)；1 | [interrupt / Command](./langgraph_impl/adapter.py#L70)；2 | 待实现；— | 待实现；— |
| Tool | [ToolRunner](./baseline/adapter.py#L35)；2 | [tool node](./langgraph_impl/agent.py#L47)；1 | 待实现；— | 待实现；— |
| MCP | [外部 adapter 可接](./baseline/adapter.py)；1 | 待实现于 Lab；— | 待实现；— | 待实现；— |
| Context controllability | [ContextBuilder](../src/aiapp/runtime/context.py)；2 | [message state](./langgraph_impl/agent.py#L22)；1 | 待实现；— | 待实现；— |
| Observability | [事件归一化](./baseline/adapter.py#L42)；1 | [事件归一化](./langgraph_impl/adapter.py#L15)；1 | 待实现；— | 待实现；— |
| Durable Execution | [文件恢复](./baseline/adapter.py#L28)；1 | [SQLite checkpoint](./langgraph_impl/adapter.py#L39)；2 | 待实现；— | 待实现；— |
| Deployment | [Python + 外部存储](./baseline/adapter.py)；2 | [额外 graph / SQLite 依赖](./langgraph_impl/adapter.py)；1 | 待实现；— | 待实现；— |
| Debuggability | [普通 Python 调试](./baseline/adapter.py)；2 | [graph state 查询](./langgraph_impl/adapter.py#L44)；1 | 待实现；— | 待实现；— |
| Vendor / Framework Lock-in | [协议边界](./labkit/protocol.py#L37)；2 | [LangGraph 类型](./langgraph_impl/adapter.py#L3)；1 | 待实现；— | 待实现；— |

## 如何读表

1. 先看需求：如果核心是跨进程暂停恢复，Checkpoint、HITL 和 Durable Execution 的证据权重最高。
2. 再看缺口：`2` 不代表“自动正确”，只代表框架提供了可验证的原语；工具幂等、租户权限和业务状态仍归应用代码。
3. 最后看 lock-in：把原生对象漏到业务层，会让迁移成本从一格变成整条调用链。共同协议的价值是限制这种泄漏。

## 选型工作表

| 问题 | 你的答案 |
|---|---|
| 任务是固定 workflow，还是需要模型探索？ |  |
| 必须跨进程暂停 / 恢复吗？最长暂停多久？ |  |
| 哪些动作有副作用？批准发生在选工具后还是更早？ |  |
| 业务状态和框架 checkpoint 谁是权威？ |  |
| 是否需要看到并修改发给模型的完整上下文？ |  |
| MCP、OpenTelemetry、部署平台是否已有组织标准？ |  |
| 两年后换模型或框架，哪些边界必须保持不变？ |  |
| 哪个假设最可能翻盘？如何在一周内验证？ |  |

完成 Lab 时，在表格后追加一段不超过一页的结论：需求约束、关键证据、选择、放弃的替代方案和退出条件。不要写总分或排名。
