---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: capability-ecosystem
tier: deep-dive
estimated_time: 约 25 分钟
---

# 11 多智能体、Handoff 与 Racing

> 多 Agent 的价值是隔离职责和上下文，不是把一个循环拆成几个名字。交接、视图和仲裁必须由运行时负责。

<details class="case" markdown="1">
<summary>例子：两个 Agent 并行查资料，返回相互矛盾的结论，系统却随机采用先到的那个</summary>

并行减少了等待，却没有定义谁的输出算数、如何处理冲突和怎样把结果写进 trace。先到先得只是一个隐藏的仲裁规则。

!!! note "构造的例子"
    竞速场景用于说明并行不是仲裁策略；真实系统应按风险选择合并规则。

</details>

## Handoff 是一份运行时契约

交接至少写清：任务目标、输入事实、允许的工具、输出格式、预算、回传条件和失败责任。不要把整个历史原样转交；接收方应得到与职责匹配的视图。

```text
Router → Specialist A → 结果 / 失败原因
      ↘ Specialist B → 结果 / 失败原因
      → Deterministic arbiter → final state
```

一个 Agent 不能决定自己是否获得更多权限，也不能决定另一个 Agent 的结果自动生效。

## 什么时候不要拆

工具很少、上下文没有清晰边界、并行结果没有明确合并规则时，拆分只会增加消息、状态和 trace。先用一个 Agent 加确定性校验，通常更容易测。

## 怎么测

用同一批任务比较单 Agent、串行 handoff 和并行 racing：

- 交接输入是否包含完成任务所需的事实；
- 是否出现权限扩大或历史泄露；
- 冲突是否按固定规则处理；
- 总延迟、成本、失败率和 trace 是否更好。

## 参考实现与延伸

参考项目没有把 handoff 作为主线运行时能力，而是在 [Framework Lab](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/framework-lab) 对照状态与交接边界（核对日期 2026-09-10）。可对照 [OpenAI Agents handoffs](https://openai.github.io/openai-agents-python/handoffs/)（访问日期 2026-09-10）。

---

[← 上一课 10](../long-horizon-tasks/README.md) · [下一课 12 →](../mcp/README.md)
