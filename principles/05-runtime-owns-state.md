---
status: complete
---

# 原则 05｜状态由运行时持有，分清对话、任务、业务、长期记忆四类

> 模型没有记忆。它每次看到的只是运行时递给它的那一串消息。状态在哪、长什么样、谁能改，全是运行时的决定。

## 主张

Agent 涉及的状态有四类，来源和生命周期完全不同，混在一起是大多数"Agent 行为诡异"问题的根源：

| 类别 | 是什么 | 谁是权威 | 生命周期 |
|---|---|---|---|
| 对话状态 | 消息、工具调用与结果 | 运行时的事件线程 | 一次会话 |
| 任务状态 | 走到哪一步、在等什么、剩多少预算 | 从事件线程推导 | 一次运行 |
| 业务状态 | 订单、审批、文件等事实 | 业务数据库 | 独立于 Agent |
| 长期记忆 | 跨会话的用户偏好、经验 | 记忆存储，带来源和删除策略 | 跨会话 |

两条推论：

1. **任务状态不要单独存。** 12-factor 的 factor 05 说得很直接：当前步骤、等待状态、重试次数这些"执行状态"，都是"已经发生了什么"的元数据，可以从事件历史算出来。单独维护一份，就要保证两份同步，这是给自己挖坑。
2. **业务状态不要放进 Agent 状态里。** 模型说"订单已发货"，运行时要去订单系统查，而不是相信线程里某条工具结果。线程是发生过什么的记录，不是事实的权威来源。

## 违反它会怎样

- **状态散落在局部变量里。** 循环里用几个变量记步数、记上次的工具结果、记"是否等用户确认"。进程一重启全没了，想暂停恢复要把每个变量都想一遍怎么序列化。
- **执行状态和事件历史各存一份。** 数据库里 `status="waiting_for_user"`，但事件历史里那条 `human_input_requested` 因为一次部分失败没写进去。恢复时两边打架，Agent 卡死或重复提问。
- **把工具返回当业务事实缓存。** 线程里有一条"库存 5 件"的工具结果，十分钟后模型据此承诺用户"有货"。库存早就是零了。
- **长期记忆没有来源。** 记忆里写着"用户不吃辣"，没人知道是哪次对话、模型推断还是用户明说的。用户否认时无法追溯，也无法定向删除。

## 最小做法

一个 append-only 的事件列表当唯一事实来源，其他一切是它的 fold：

```python
@dataclass
class Thread:
    events: list[Event]

    def to_messages(self) -> list[Message]:      # what the model sees
        ...
    def status(self) -> str:                      # running / paused / finished, derived
        for e in reversed(self.events):
            if e.type == "run_finished": return "finished"
            if e.type == "human_input_requested": return "paused"
        return "running"
    def pending_tool_calls(self) -> list[ToolCall]:  # asked for, no result yet
        ...
```

序列化这个列表就是序列化整次运行；加载它就能从任意一点继续。业务事实每次用之前重新查；长期记忆单独存，每条带来源和时间。

## 对照

- 参考：[12-factor-agents · factor 05](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-05-unify-execution-state.md)、[factor 12](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-12-stateless-reducer.md)（访问日期 2026-09-04）；[langchain-academy · module-2 state schema 与 reducers](https://github.com/langchain-ai/langchain-academy/tree/main/module-2)（访问日期 2026-09-04）
- 相关课程：[07 Agent State 与 Runtime](../lessons/07-agent-state-and-runtime/README.md)、[15 Memory](../lessons/15-memory/README.md)

---

[← 原则总览](./README.md)
