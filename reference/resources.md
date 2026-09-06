# 外部资料

> 每条标访问日期。时间敏感的信息不写成永久事实，引用前先自己打开看一眼。

这一页分四层，用途不同，别混着看：**知识地图**告诉你还有什么不知道，**官方文档**是写代码时的唯一依据，
**真实系统**让你看见机制在生产里的样子，**论文**只在需要追溯出处时才读。

## 知识地图：课程参考的仓库

拿来对照"我的地图上还缺哪一块"，不是拿来逐行读的。

| 仓库 | 用途 | 访问日期 |
|---|---|---|
| [humanlayer/12-factor-agents](https://github.com/humanlayer/12-factor-agents) | Agent 工程原则 | 2026-09-04 |
| [microsoft/ai-agents-for-beginners](https://github.com/microsoft/ai-agents-for-beginners) | Agent 知识地图 | 2026-09-04 |
| [langchain-ai/langchain-academy](https://github.com/langchain-ai/langchain-academy) | State / Graph / Checkpoint 机制 | 2026-09-04 |
| [openai/openai-cookbook](https://github.com/openai/openai-cookbook) | 具体技术点示例库 | 2026-09-04 |
| [anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks) | 同上，Anthropic 侧；工具调用和 RAG 两组 notebook 最有用 | 2026-09-06 |
| [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners) | GenAI 应用通识 | 2026-09-04 |
| [mlabonne/llm-course](https://github.com/mlabonne/llm-course) | LLM Engineer 知识树 | 2026-09-04 |
| [rasbt/LLMs-from-scratch](https://github.com/rasbt/LLMs-from-scratch) | 模型原理 | 2026-09-04 |

## 厂商官方文档：该读的是这几页

**二手教程会过期，字段名只有官方文档说了算。** 下面两张表列的是页面，不是首页——每一页对应课程里的一个具体决策。
课程默认走 OpenAI 兼容协议，所以 OpenAI 的几页是通用参考；Anthropic 的几页里有几项是它独有的机制，
换供应商时要知道自己失去了什么。

| OpenAI | 读它回答什么 | 对应课 | 访问日期 |
|---|---|---|---|
| [Function calling](https://platform.openai.com/docs/guides/function-calling) | 工具怎么定义、并行调用怎么回、strict 模式限制了什么 | 05 | 2026-09-06 |
| [Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs) | schema 约束的确切写法，以及它和"提示模型输出 JSON"的区别 | 02 | 2026-09-06 |
| [Prompt caching](https://platform.openai.com/docs/guides/prompt-caching) | 什么样的前缀能命中缓存，命中之后省的是哪部分钱 | 08、19 | 2026-09-06 |
| [Reasoning models](https://platform.openai.com/docs/guides/reasoning) | reasoning token 怎么计费、effort 怎么选、和工具调用怎么配合 | 01、02 | 2026-09-06 |
| [Batch API](https://platform.openai.com/docs/guides/batch) | 离线批处理的提交与回收；能接受延迟时单价明显更低 | 19、21 | 2026-09-06 |
| [Agents SDK 文档](https://openai.github.io/openai-agents-python/) | handoff、guardrail、session 三个词的官方定义 | 10、20 | 2026-09-06 |

| Anthropic | 读它回答什么 | 对应课 | 访问日期 |
|---|---|---|---|
| [Tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use/overview) | `tool_use` 和 `tool_result` 怎么配对，错误怎么回喂 | 05 | 2026-09-06 |
| [Prompt caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) | 缓存断点放在哪、最短长度和有效期各是多少 | 08 | 2026-09-06 |
| [Extended thinking](https://docs.claude.com/en/docs/build-with-claude/extended-thinking) | thinking block 长什么样，多轮工具调用里怎么传递 | 02、08 | 2026-09-06 |
| [Claude Agent SDK 概览](https://docs.claude.com/en/api/agent-sdk/overview) | 一个厂商自己实现的 agent 循环，边界划在哪 | 06、07 | 2026-09-06 |
| [Claude Code · Hooks](https://docs.claude.com/en/docs/claude-code/hooks) | 怎么在 agent 循环里插确定性拦截点，而不是写进提示词 | 06、20 | 2026-09-06 |

**这两家的文档页会改，字段名也会改。** 落到代码里的字段，以你写代码那天打开的页面为准。

## 真实系统：agent harness

编码 agent 是目前跑得最久、被用得最狠的一类 Agent 产品。读它们**不是为了学架构，是为了看第 05～12 课的机制在真机上长什么样**：
一个工具的参数该怎么设计、循环凭什么停、上下文满了先扔什么、权限边界画在哪。下面每行只写一件最值得看的事。

| 项目 | 语言 | 值得看的一件事 | 对应课 |
|---|---|---|---|
| [openai/codex](https://github.com/openai/codex) | Rust | 沙箱和审批分级：哪些动作直接做、哪些要问 | 06、20 |
| [cline/cline](https://github.com/cline/cline) | TypeScript | 计划与执行分成两种模式；文件改动走 diff 而不是整文件重写 | 09、22 |
| [Aider-AI/aider](https://github.com/Aider-AI/aider) | Python | repo map：怎么在有限上下文里表示一个大代码库 | 08、13 |
| [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | Python | 动作与观察成对的事件流，就是第 07 课那份事件记录 | 07、18 |
| [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | Python | agent-computer interface：工具是为模型设计的，不是为人 | 05 |
| [block/goose](https://github.com/block/goose) | Rust | 扩展能力全部走 MCP，是第 11 课协议价值的一个实例 | 11、12 |
| [anthropics/claude-code](https://github.com/anthropics/claude-code) | — | 本体不开源，这个仓库是 CHANGELOG、插件与示例；机制看上面的官方文档 | 06、12 |
| [agents.md](https://agents.md/) | — | 一份写给编码 agent 的项目说明文件约定 | 03、12 |

访问日期均为 2026-09-06。**这几个项目迭代很快**，上面写的是当天打开时的形态，隔几个月再看可能已经换了做法。

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
- [Anthropic · Writing effective tools for AI agents](https://www.anthropic.com/engineering/writing-tools-for-agents)（访问日期 2026-09-06）：工具的名字、描述和返回值怎么写，模型才用得对。第 05 课「工具是契约」落到字面上的部分。
- [Anthropic · How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)（访问日期 2026-09-06）：多 Agent 的收益和它的 token 代价，第 10 课判断「要不要再加一个 Agent」时看这篇。
- [Anthropic · Claude Code best practices](https://www.anthropic.com/engineering/claude-code-best-practices)（访问日期 2026-09-06）：从使用约定反推一个成熟 harness 的设计，第 06、12 课。
- [OpenAI · A practical guide to building agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)（PDF，访问日期 2026-09-06）：单 Agent 什么时候该拆成多 Agent，以及 guardrail 的分层，第 09、21 课。

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
| 厂商文档的页面地址与字段名 | 快 | 每季度 |
| 上面那几个 agent harness 的做法 | 快 | 每季度 |
| Agent 框架的持久化与 trace 支持 | 中 | 半年 |
| embedding 与 reranker 的选择 | 中 | 半年 |
| MCP 与 A2A 的协议版本 | 中 | 半年 |
| 上面那几份协议规范本身 | 慢 | 一年 |

课程当前的选型结论见[技术选型](./stack.md)，框架横向对比见[框架一览](./frameworks.md)，两处都标了核对日期。
