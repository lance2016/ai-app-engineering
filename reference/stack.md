# 工具栈与选型

> 来源：原 Vault `28-AI应用开发实际工具栈与选型`，待迁入。这里只记录「选了什么、为什么、什么时候该换」。

## 课程默认栈

| 层 | 选择 | 理由 | 什么时候换 |
|---|---|---|---|
| 语言与包管理 | Python 3.12 + uv | 读者群体；uv 快且锁定可复现 | 无 |
| Web | FastAPI + Pydantic v2 | async 原生、类型即校验、SSE/WS 直接支持 | 无 |
| 测试 | pytest | 事实标准 | 无 |
| 数据库 | PostgreSQL + pgvector | 一个库同时管业务数据和向量，少一个组件 | 向量量级超过千万或需要专门的过滤性能时评估专用向量库 |
| 缓存与队列 | Redis | 状态、幂等键、简单队列 | 需要严格顺序和重放时换消息队列 |
| 模型接入 | `openai` SDK 走 OpenAI 兼容协议，包在 adapter 后面；默认 fake adapter，真实示范用 DeepSeek | 不绑供应商；离线可跑；DeepSeek 国内可访问且价格低 | 需要 Anthropic 原生特性（如 prompt caching 细节、server tools）时另加一个 adapter |
| Agent | 普通 Python 状态机 | 先懂机制再选框架 | 项目需要持久化 checkpoint 和 HITL 时评估 LangGraph 等；对比见 [Agent 框架对比与选型](../lessons/09-workflow-vs-agent/bonus/agent-frameworks-compared.md) |
| 可观测 | 结构化日志 + OpenTelemetry + Arize Phoenix | 通用 trace 标准；Phoenix 本地起得快 | 需要团队协作和评测管理时比较 Langfuse |
| 容器 | Docker Compose | 一条命令起依赖 | 无 |

## 选型原则

1. 同一阶段最多引入一个新平台。
2. 先用最小工具直接实现，再用框架重构一次，比较收益和隐藏成本。
3. 记录为什么选它，也记录什么时候该退出。
4. 装上了软件不等于掌握了能力。
