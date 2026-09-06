---
status: complete
updated: 2026-09-05
---

# Agent 框架一览与选型标准

> 课程正文全部用普通 Python，是为了让你先看清机制。看清之后再选框架，你会知道自己在为什么付费、放弃什么。
>
> 这份对比给的是**判断标准和一张快照，不是排名**。框架迭代很快，特性以 2026-09-05 为准，动手前以官方文档为准。想深入某一个，直接去它的官网，比看任何二手对比都可靠。

## 先问自己：需要框架吗

第 05～08 课讲的机制，用普通 Python 写下来不到 500 行，已经覆盖了工具契约、循环、预算、失败路由。**一个框架至少要在下面某一项上明显省事**，才值得引入它带来的抽象和升级成本：

- **持久化执行**：循环中途暂停，几小时后从同一个点恢复，进程重启也不丢。自己写要处理 checkpoint 序列化、幂等重入、版本迁移，是真正的工作量。
- **人工介入**：在某一步停下等人批准，批准后继续。和上一条是同一件事的两面。
- **事件流**：把每一步的中间状态推给前端。自己写不难，但和持久化耦合后就复杂了。
- **多 Agent 编排原语**：handoff、子图、并行分支的汇合。
- **供应商生态绑定**：你已经决定只用某一家模型，它的 SDK 里有你需要的托管能力。

**这五项一个都不需要，普通 Python 加第 07 课的状态存储就够了。**

## 判断一个框架的六个问题

拿任何框架，用一个下午回答这六个问题。每个问题对应课程里的一课：

| 问题 | 看什么 | 对应课 |
|---|---|---|
| 工具怎么定义、参数怎么校验、错误怎么回给模型 | 有没有 schema 校验；工具异常是抛出还是变成结果；能否按请求控制可见工具 | [05](../lessons/05-tool-calling/README.md) |
| 循环由谁控制、怎么停 | 能不能自己写循环；有没有步数 / token / 时间预算；能不能在任意一步跳出 | [06](../lessons/06-agent-loop/README.md) |
| 状态存在哪、怎么恢复 | state 的数据结构是否显式；checkpoint 存哪、怎么换后端；恢复时是否重放副作用 | [07](../lessons/07-agent-state-and-runtime/README.md) |
| 上下文怎么组装 | 历史裁剪和压缩是否可控；能否看到最终发给模型的完整消息 | [08](../lessons/08-context-engineering-for-agents/README.md) |
| 多 Agent 怎么交接 | handoff 时历史给多少；子 Agent 的状态是否隔离；并行分支怎么汇合 | [10](../lessons/10-multi-agent-handoff/README.md) |
| 出了问题怎么看 | 有没有原生 trace；能不能接 OpenTelemetry 而不是只接自家平台 | [19](../lessons/19-observability/README.md) |

**一个框架回答不上其中两个以上，说明它的抽象层把你需要看的东西盖住了。**

## 快照

「控制流模型」是最重要的一列，它决定了你写代码时的心智模型。

| 框架 | 官方文档 | 控制流模型 | 持久化 / HITL | 模型绑定 | 一句话定位 |
|---|---|---|---|---|---|
| LangGraph | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) | 显式图：节点、边、条件边、子图 | 内置 checkpointer，支持中断和 time travel | 无 | 需要持久化执行和人工介入时的默认选项 |
| OpenAI Agents SDK | [openai.github.io/openai-agents-python](https://openai.github.io/openai-agents-python/) | Agent 循环 + handoff | 有 session 抽象；深度持久化靠自己或托管平台 | 主打 OpenAI，可接兼容接口 | 轻量，handoff 原语清晰 |
| Claude Agent SDK | [docs.claude.com/en/api/agent-sdk](https://docs.claude.com/en/api/agent-sdk/overview) | 内置 agent 循环（与 Claude Code 同源） | 会话由 SDK 管理 | Anthropic | 直接复用 Claude Code 的工具和权限模型 |
| Google ADK | [google.github.io/adk-docs](https://google.github.io/adk-docs/) | Agent 树 + 顺序 / 并行 / 循环编排器 | 有 session 服务，可换后端 | 主打 Gemini，支持其他模型 | 编排器类型丰富，自带评测工具 |
| Microsoft Agent Framework | [learn.microsoft.com/agent-framework](https://learn.microsoft.com/en-us/agent-framework/) | Agent + 图式 workflow | 有 checkpoint 设计 | 无，偏 Azure 生态 | 企业场景，.NET 和 Python 双栈 |
| PydanticAI | [ai.pydantic.dev](https://ai.pydantic.dev/) | 类型驱动的 agent 循环，可接图 | 有持久化方向的设计 | 无 | 类型安全和结构化输出做得最顺手 |
| CrewAI | [docs.crewai.com](https://docs.crewai.com/) | 角色 + 任务 + 流程 | 有 flow 状态 | 无 | 角色型多 Agent 原型起得最快 |
| LlamaIndex Workflows | [developers.llamaindex.ai](https://developers.llamaindex.ai/python/framework/module_guides/workflow/) | 事件驱动：`@step` 处理事件、产出事件 | 有 context 序列化 | 无 | 适合步骤分支多的流程 |
| smolagents | [huggingface.co/docs/smolagents](https://huggingface.co/docs/smolagents/) | 模型写代码当动作（code agent） | 弱 | 无，偏 Hugging Face 生态 | 极简，用来理解 code-as-action 范式 |
| Agno | [docs.agno.com](https://docs.agno.com/) | Agent + team + workflow | 有存储抽象 | 无 | 强调运行时和多 Agent 平台化 |

三点说明：

- **星数不反映适合你。** CrewAI 的 star 最多，但它的抽象层最厚，上面六个问题里有几个不容易回答。
- **三家模型厂商的 SDK 各有一套 agent 循环。** 选它们的理由通常不是框架本身，而是背后的托管能力和与自家模型特性的贴合。代价是换模型时要连框架一起换。
- **LangGraph 和 LlamaIndex Workflows 代表两种控制流心智模型**：前者是「画一张图」，后者是「发事件、处理事件」。前者路径可见，后者扩展分支容易。选哪个看你的团队更习惯哪种思维。

## 选型建议

| 你的情况 | 建议 |
|---|---|
| 还在学机制，或任务在 10 步以内、不需要跨请求恢复 | 普通 Python，第 05～08 课的机制直接用 |
| 需要暂停等人、进程重启后恢复、看历史某一步的状态 | LangGraph |
| 已经决定只用一家模型，且要用它的托管工具、会话或评测 | 该厂商的 Agent SDK |
| 团队重视类型和结构化输出，不想要厚抽象 | PydanticAI |
| 流程分支多、步骤之间松耦合，团队习惯事件驱动 | LlamaIndex Workflows |
| 想快速验证一个多角色分工的想法 | CrewAI，验证完再决定要不要重写 |
| 想理解「让模型写代码当动作」这个范式 | smolagents，读源码比用它更有价值 |

无论选哪个，先在第 07 课的状态模型上想清楚一件事：**框架的 state 和你的业务状态是什么关系。框架的 checkpoint 不是你的数据库。**

## 一个来自生产项目的观察

语音机器人项目用的是事件驱动的 workflow 框架，每个 `@step` 接收一类事件、产出下一类事件。

好处是加一个分支只需要加一个 step，不用改别人的代码。踩过的坑是：**事件驱动让「当前走到哪一步」变得不直观**，排障时要靠 trace 而不是读代码。所以第 19 课的可观测性对事件驱动架构不是可选项。

另一个教训：框架的 agent 循环和自己写的双模型竞速逻辑叠在一起后，**谁负责停止变得模糊**，最后是把停止条件全部收回到自己的代码里才稳定。这印证了 factor 08——控制流自己拿着。

## 延伸阅读

- [12-factor-agents · factor 08 Own your control flow](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-08-own-your-control-flow.md)（访问日期 2026-09-04）：为什么控制流不该交给框架。
- [ai-agents-for-beginners · 02 Explore Agentic Frameworks](https://github.com/microsoft/ai-agents-for-beginners/blob/main/02-explore-agentic-frameworks/README.md)（访问日期 2026-09-04）：微软视角的框架介绍，偏自家生态，但「什么时候该用框架」那一节值得读。
- [Anthropic · Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)（访问日期 2026-09-05）：「从最简单的方案开始」的出处。

---

参考实现见 [ai-app-engineering-ref](https://github.com/lance2016/ai-app-engineering-ref)
