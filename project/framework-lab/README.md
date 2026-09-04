---
status: outline
kind: lab
depends_on: project/m3；lessons/05–12；回顾 18, 19
---

# Framework & Architecture Lab

> 主线用普通 Python 把机制讲完，M3 用普通 Python 把一个能干活、能停、能续的 Agent 做出来。这个 Lab 拿同一个需求，在三个主流框架上各实现一遍，跑同一套一致性测试，然后按十二个维度逐格对照。目标不是选出最好的框架，是让你下次面对选型时知道该问什么、去哪找证据。

## 为什么需要

不用框架的理由这门课已经讲够了：控制流自己拿着、上下文自己拼、状态自己存。但生产团队最终多数会用框架，理由通常是持久化执行、人工介入、事件流、多 Agent 原语这四样里的某一样。用框架的代价是抽象层盖住了你需要看的东西，而不同框架盖住的地方不一样。只有在同一个需求上把它们都做一遍，差别才看得见。

## 共同需求

一个审批型任务 Agent，规格在 `spec.md`（待写）。它必须：

- 用同一批只读工具直接调用，副作用工具必须暂停等人批准后再执行
- 进程被 `kill -9` 后能从断点续上，已执行的工具不重跑
- 每一步以事件流推给客户端，事件类型与第 07 课的 `Thread` 一致
- 接入一个 MCP Server（第 11 课的 toy server）
- 处理 double texting，策略可配置
- 带 OpenTelemetry trace，span 属性遵循 GenAI 语义约定
- 通过 M1 同一套 HTTP 接口暴露，离线用 fake 模型可跑通全部测试

## 三个实现

| 目录 | 框架 | 为什么选它 | 离线怎么跑 |
|---|---|---|---|
| `00-baseline/` | 普通 Python，即 M3 的 `aiapp.runtime` | 参照物：不用框架要写多少、哪里最痛 | 本来就是 fake adapter |
| `01-langgraph/` | LangGraph | 显式图、内置 checkpointer、中断与 time travel，"持久化执行"路线的代表 | 包一个 `BaseChatModel` 子类回放 fake 剧本 |
| `02-openai-agents-sdk/` | OpenAI Agents SDK | 厂商 SDK 的代表，handoff 原语最清晰；走 OpenAI 兼容协议所以 DeepSeek 也能接 | 实现 `Model` 接口回放 fake 剧本 |
| `03-claude-agent-sdk/` | Claude Agent SDK | 另一种厂商路线：内置循环、工具和权限模型与 Claude Code 同源，锁定最深也最省事 | mock SDK 的消息流 |

每个实现目录固定四样东西：`README.md`（本课概念到框架概念的映射表、顺手的地方、别扭的地方、锁定点）、`agent.py`、`adapter.py`（实现共同的 `AgentRuntime` 协议让一致性测试能跑）、十二维度的自评。

## 十二个维度

| 维度 | 看什么 | 对应课 |
|---|---|---|
| Control Flow | 循环由谁控制、能否在任意一步跳出、图还是事件还是循环 | 06, 09 |
| State | state 的数据结构是否显式、业务状态和框架状态什么关系 | 07 |
| Checkpoint | 存哪、能否换后端、恢复时是否重放副作用 | 07, M2 |
| Human-in-the-loop | 能否在"选好工具"和"执行工具"之间暂停 | 07 |
| Tool | schema 校验、异常怎么回给模型、按请求控制可见工具 | 05 |
| MCP | 原生支持还是自己接、断连怎么处理 | 11 |
| Context 控制 | 能否看到并改写发给模型的完整消息、历史裁剪是否可控 | 08 |
| Observability | 原生 trace 还是只接自家平台、能否接 OpenTelemetry | 18 |
| Durable Execution | 进程重启后从哪继续、靠自己还是靠外部引擎 | 07, 19 |
| Deployment | 单进程、API 加 worker、还是托管平台；依赖多少基础设施 | 19, M5 |
| Debuggability | 出了问题读代码还是读 trace、能否单步 | 18 |
| Vendor / Framework Lock-in | 换模型、换框架、换平台各要改多少 | 原则 12, 23 |

评分卡在 `scorecard.md`（待写）。每格附代码行链接作为证据，不打总分，不排名。最后一页是一张给读者的选型工作表。

## 一致性测试

`tests/framework-lab/conformance/` 通过共同的 `AgentRuntime` 协议跑在每个实现上：暂停恢复、崩溃恢复、幂等重放、double texting 三策略、MCP 断连、事件流与线程一致。哪个实现过不了哪条，就是那一格评分卡的证据。

## 依赖

框架依赖单独放 `frameworks` 依赖组，`uv sync --group frameworks` 才装，主线课程不受影响。三个框架都要钉版本并标日期。

## 学习位置

做完 M3 之后做 Lab，那时你刚用普通 Python 写完同样的东西，对照最清楚。学完 18、19 再回来重打 Observability、Deployment 两格。Capstone 3 要求用普通 Python 和一个框架各做一遍，选哪个框架用这里的评分卡决定。

## 目录

| # | 内容 | 状态 |
|---|---|---|
| 00 | [框架全景与选型标准](./00-landscape.md) | draft |
| spec | 共同需求（待写） | outline |
| 00-baseline | M3 参照实现（待 M3） | outline |
| 01-langgraph | （待写） | outline |
| 02-openai-agents-sdk | （待写） | outline |
| 03-claude-agent-sdk | （待写） | outline |
| scorecard | 十二维评分卡（待写） | outline |

---

[← 项目总览](../README.md)
