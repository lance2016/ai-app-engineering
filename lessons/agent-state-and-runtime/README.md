---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: runtime
tier: core
estimated_time: 约 35 分钟
---

# 07 Agent State 与 Runtime：持久化、暂停恢复与人工介入

> 状态不是聊天记录的别名。它要回答：运行到哪一步、正在等什么、外部动作是否已经发生，以及重启后从哪里继续。

<details class="case" markdown="1">
<summary>例子：钱已经转出，进程却在写入结果前崩溃</summary>

恢复时本地只知道“工具没有结果”。如果直接重跑，可能重复转账；如果假设没执行，可能漏掉结果。checkpoint 能保存本地事件，但不能替外部系统证明副作用是否发生。

!!! note "构造的例子"
    崩溃点用于说明未知状态；真实系统需要根据外部接口能力选择查询、幂等或人工对账。

</details>

## 四类状态不要混在一起

| 状态 | 权威来源 | 生命周期 |
|---|---|---|
| 对话 | 事件线程中的消息与工具结果 | 一次会话 |
| 任务 | 从事件推导的步骤、等待和预算 | 一次运行 |
| 业务 | 订单、文件、权限等业务数据库 | 独立于 Agent |
| 长期记忆 | 带来源、时间和删除策略的存储 | 跨会话 |

模型输出的清单是对话事件；清单哪项已经验收，是任务状态。业务数据库才是订单事实，不能相信历史中的一句“已发货”。

## 事件线程是恢复的入口

```text
run_started
→ assistant_message
→ tool_call_requested
→ tool_started
→ tool_finished
→ run_finished
```

事件追加后不可随意改写，当前状态由它们 fold 出来。暂停时记录 `human_input_requested`，恢复时追加用户决定，再从下一个未完成步骤继续。

## checkpoint 保证不了外部副作用

本地可以保证事件不重复，但“执行外部动作”和“写入执行结果”通常不是一个事务。恢复策略按风险排列：

1. 外部接口支持幂等键：带同一业务键重试。
2. 可以查询状态：先查成没成功，再决定下一步。
3. 两者都不支持：标记未知，进入人工对账，不盲目重跑。

事件是发生过什么的记录，不是恢复时要再次执行的命令。

## 怎么测

把进程停在以下位置后重启：事件写入前、工具调用前、外部动作完成后、结果记录前、人工确认等待中。检查：

- 本地事件是否能还原唯一的运行状态；
- 需要人的运行是否不会偷偷继续；
- 外部副作用是否不会因恢复重复发生；
- 客户端是否能看到同一条事件线程。

## 参考实现与延伸

参考实现的事件存储、checkpoint 和人工介入在 [M2 State and Storage](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m2-state-and-storage)（核对日期 2026-09-10）。事件状态的拆分可对照 [12-factor-agents](https://github.com/humanlayer/12-factor-agents)（访问日期 2026-09-10）。

---

[← 上一课 06](../agent-loop/README.md) · [下一课 08 →](../context-engineering-for-agents/README.md)
