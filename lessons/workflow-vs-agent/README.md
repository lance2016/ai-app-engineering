---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: runtime
tier: core
estimated_time: 约 30 分钟
---

# 09 Workflow 还是 Agent：架构模式

> 先问“能不能把路径写死”。Workflow 用代码控制步骤，Agent 把部分路径选择交给模型；这是可预测性和灵活性的取舍，不是先进和落后。

<details class="case" markdown="1">
<summary>例子：固定的抽取—校验—报告流程被做成 Agent，结果偶尔跳过校验</summary>

流程本来只有三步，Agent 却自行决定是否重做、是否省略校验。系统因此更难测，延迟和成本也上升。

!!! note "构造的例子"
    流程用于说明固定路径不应交给模型；实际判断要看步骤是否真的随任务变化。

</details>

## 两种模式的边界

| 问题 | Workflow | Agent |
|---|---|---|
| 谁决定下一步 | 代码 | 模型建议，代码放行 |
| 路径 | 预先定义 | 根据中间结果变化 |
| 可预测性 | 高 | 较低 |
| 成本与测试 | 容易估算 | 需要预算和轨迹评测 |

能写成状态机的流程先写代码。只有当步骤依赖开放式理解、分支组合无法穷举、或任务形状每次明显不同，才增加 Agent 决策。

## 从简单到复杂

常见的升级顺序是：一次调用 → 顺序串联 → 路由 → 并行 → 编排多个子任务 → 自治循环。每向右走一步，都要说明前一步解决不了什么，并补上新的终止、预算和评测。

多 Agent 不是默认的下一步。它增加交接协议、状态视图、仲裁和 trace；只有上下文或职责确实需要隔离时才值得。

## 怎么测

同一份任务集同时记录：

- 路径是否稳定，是否出现不必要的分支；
- 每条路径的成功率、步骤数、延迟和成本；
- 模型决定的步骤是否都经过代码守卫；
- 失败时能否指出是路径设计还是模型判断导致。

如果 Workflow 和 Agent 在效果相同，优先选择步骤更少、边界更确定的那个。

## 参考实现与延伸

参考实现把工具审批和固定流程放在 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow)（核对日期 2026-09-10）。可对照 [Anthropic Building effective agents](https://www.anthropic.com/research/building-effective-agents)（访问日期 2026-09-10）。

---

[← 上一课 08](../context-engineering-for-agents/README.md) · [下一课 10 →](../long-horizon-tasks/README.md)
