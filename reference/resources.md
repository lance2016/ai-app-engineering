# 外部资料

> 每条标访问日期。时间敏感的信息不写成永久事实，引用前先自己打开看一眼。

## 课程参考的仓库

| 仓库 | 用途 | 访问日期 |
|---|---|---|
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程原则 | 2026-09-04 |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | Agent 知识地图 | 2026-09-04 |
| [langchain-ai/langchain-academy](https://github.com/langchain-ai/langchain-academy) | State / Graph / Checkpoint 机制 | 2026-09-04 |
| [openai/openai-cookbook](https://github.com/openai/openai-cookbook) | 具体技术点示例库 | 2026-09-04 |
| [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | GenAI 应用通识 | 2026-09-04 |
| [mlabonne/llm-course](https://github.com/mlabonne/llm-course) | LLM Engineer 知识树 | 2026-09-04 |
| [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 模型原理 | 2026-09-04 |

## 协议与规范

写代码时以这些为准，不以任何二手教程为准。

| 规范 | 管什么 | 对应课 | 访问日期 |
|---|---|---|---|
| [Model Context Protocol](https://modelcontextprotocol.io/specification) | 能力接入的生命周期与消息格式 | 11 | 2026-09-04 |
| [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) | span 名与属性名 | 18 | 2026-09-04 |
| [OpenTelemetry 属性注册表 · gen_ai](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/registry/attributes/gen-ai.md) | 哪些属性名已废弃 | 18 | 2026-09-04 |
| [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) | 威胁分类的通用词汇 | 20 | 2026-09-04 |

用到协议时**记下版本号**，它们都还在演进。

## 工程实践

- [Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（访问日期 2026-09-04）：Workflow 与 Agent 模式的分类，第 09 课的骨架。
- [Anthropic · Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（访问日期 2026-09-04）：attention budget 和 just-in-time 两个说法的出处，第 08 课。

## 论文

只列课程正文真的引用过的，读摘要和指定的那一节就够。

| 论文 | 读哪部分 | 对应 |
|---|---|---|
| [Attention Is All You Need](https://arxiv.org/abs/1706.03762) | 第 3.2 节 | F03 |
| [Sentence-BERT](https://arxiv.org/abs/1908.10084) | 第 3 节训练目标 | F02、04 |
| [Matryoshka Representation Learning](https://arxiv.org/abs/2205.13147) | 摘要与图 1 | F02、04 |
| [RAG](https://arxiv.org/abs/2005.11401) | 摘要与图 1 | 13 |
| [ReAct](https://arxiv.org/abs/2210.03629) | 摘要与图 1 | 06 |

## 需要定期核查的内容

下面这些**没有长期正确的答案**，课程里凡是写到都必须带日期。自己维护技术选型文档时，同样按这个清单排查。

| 内容 | 变化速度 | 建议核查周期 |
|---|---|---|
| 模型能力、上下文长度、价格 | 快 | 每季度 |
| 推理服务与量化方案 | 快 | 每季度 |
| Agent 框架的持久化与 trace 支持 | 中 | 半年 |
| embedding 与 reranker 的选择 | 中 | 半年 |
| MCP 与 A2A 的协议版本 | 中 | 半年 |
| 上面那几份协议规范本身 | 慢 | 一年 |

课程当前的选型结论见[技术选型](./stack.md)，框架横向对比见[框架一览](./frameworks.md)，两处都标了核对日期。
