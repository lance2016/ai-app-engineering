# Baseline｜普通 Python

baseline 是 Framework Lab 的参照物：它复用 M3 的 `aiapp.runtime`，把事件线程、工具守卫和 JSON checkpoint 直接暴露出来。它不是“没有框架”，而是让读者看清引入框架之前需要自己拥有的边界。

## 概念映射

| Lab 概念 | baseline 的位置 | 观察 |
|---|---|---|
| Control Flow | `run_agent()` 的 async loop | 顺手：每个停止条件都可读、可测；代价是所有恢复分支自己维护 |
| State / Checkpoint | `Thread` + 每步 JSON | 顺手：业务事件就是历史；别扭：生产要做 schema migration、并发写和存储清理 |
| HITL | `NeedsConfirmation` / pending event | 可以精确停在“选工具后、执行前” |
| Context | `ContextBuilder` | 完全可控；上下文预算不是框架默认值 |
| Observability | 事件归一化 + M5 tracer | 可接任何 exporter；要自己定义 span 生命周期 |

## 失败行为与部署

未知工具、坏参数和工具异常都变成可回喂的结果；预算超限变成 `failed`；暂停期间的新消息变成 `rejected`。恢复时先写 `human_input`，再从事件线程继续，工具级幂等键防止副作用重放。

部署只需要 Python 服务、PostgreSQL 和 Redis。这个轻量边界适合固定 workflow、短循环和团队希望掌握全部控制流的场景。它不自动提供 MCP、图可视化或 durable execution 平台，接入这些能力就是应用团队自己的维护成本。

## Lock-in 判断

baseline 的业务层依赖 [`LabRuntime`](../labkit/protocol.py)，不依赖某个框架对象；这也是迁移时最值得保留的边界。它的“锁定”主要来自自建协议和运维代码，而不是供应商 SDK。

运行：`uv run pytest tests/project/framework_lab -q`。共同规格和评分口径见 [`../spec.md`](../spec.md) 与 [`../scorecard.md`](../scorecard.md)。
