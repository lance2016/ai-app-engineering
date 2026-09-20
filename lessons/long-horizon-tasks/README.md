---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: runtime
tier: deep-dive
estimated_time: 约 25 分钟
---

# 10 长任务与计划：目标为什么会漂，清单怎么兜住

> 长任务的难点不是多调用几次模型，而是每一步都合理时，整体目标仍可能慢慢偏掉。计划要成为运行时可检查的数据。

<details class="case" markdown="1">
<summary>例子：Agent 一直在修改文件，却忘了最初要求必须保留的兼容行为</summary>

任务变长后，模型被最近的错误和新发现吸引。它没有违反某一轮指令，却逐步换了目标。

!!! note "构造的例子"
    目标漂移用于说明长任务的控制问题；实际验收应绑定项目的测试命令。

</details>

## 清单解决的是可见性，不是正确性

计划可以记录目标、步骤、依赖和验收，但模型写“完成”不等于完成。每项都需要确定性验收：测试、文件存在、字段满足或人工确认。

```text
目标 → 生成计划 → 执行一项 → 运行验收
       ↑                         ↓
       └────失败则修正或重规划───┘
```

计划是运行时保存的状态，不是模型可以随意改松的权限。重规划时要记录旧计划、新计划和变化原因。

## 长任务的三个保险

- **边界**：每项任务有输入、输出和最大步骤。
- **检查点**：阶段完成后保存事件、产物和验收结果。
- **终止**：连续失败、预算耗尽或目标不可行时停止并交给人。

能干净拆开的任务可以交给多个小 Agent；无法拆开的任务适合一份短清单持续回注。两种方案都要保留最终验收。

## 怎么测

准备一个需要几十步的任务，注入工具失败、重启、计划修改和中途新需求。检查：

- 每一步是否有验收证据；
- 目标约束是否在压缩和重规划后仍然存在；
- 失败后是否从检查点继续而不是重复副作用；
- 最终终态是否由验收代码判定。

## 参考实现与延伸

参考实现的长任务验收在 [Capstone 3](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/capstones)（核对日期 2026-09-10）。可对照 [Anthropic Building effective agents](https://www.anthropic.com/research/building-effective-agents)（访问日期 2026-09-10）。

---

[← 上一课 09](../workflow-vs-agent/README.md) · [下一课 11 →](../multi-agent-handoff/README.md)
