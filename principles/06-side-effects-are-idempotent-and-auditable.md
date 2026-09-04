---
status: complete
---

# 原则 06｜每个副作用都要幂等、可确认、可审计

> 读操作出错可以重来，副作用出错就是事故。凡是会改变外部世界的动作，运行时必须能保证三件事：重复执行无害、高风险的先问人、事后能说清谁在什么时候因为什么做了它。

## 主张

Agent 的动作分两类：只读的和有副作用的。只读动作失败了再试一次没有代价；副作用不一样，转一笔钱、发一封邮件、删一个文件，多做一次就是多一次损失。所以副作用要额外满足三条：

1. **幂等**：同一个意图执行多次，效果和执行一次相同。运行时无法保证"执行"和"记录执行结果"是原子的，进程可能在两者之间崩掉。幂等是唯一能让重跑安全的办法。
2. **可确认**：不可逆或高风险的动作，在选好工具和执行之间暂停，问人。12-factor 的 factor 07 说得直接：联系人类也是一个工具调用，运行时看到它就存盘、通知、退出，等回答再继续。
3. **可审计**：每个副作用留一条记录，写清工具名、参数、幂等键、触发它的模型消息、是否经过确认、执行结果。出问题时能回放，被质疑时能举证。

这三条不是模型的责任。模型不知道它上一次是否已经转过账，也判断不了什么算高风险。它们是运行时的确定性代码。

## 违反它会怎样

- **重试导致双重扣款。** 工具调用超时，运行时按"瞬时错误"重试，第一次其实已经成功。没有幂等键，银行看到两笔独立的请求。
- **模型自己决定要不要确认。** 提示词里写"重要操作前先问用户"，模型大多数时候照做，偶尔不照做。那"偶尔"就是事故发生的时候。
- **恢复时重放副作用。** 从 checkpoint 恢复的实现是"把事件重新执行一遍"，于是已经发过的邮件又发了一次。事件是记录，不是指令。
- **审计只有"操作成功"四个字。** 用户投诉账户被改，日志里查到一条 `update_profile ok`，不知道参数是什么、模型为什么这么做、有没有人确认过。既没法定责，也没法防再犯。

## 最小做法

```python
@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Callable[..., Awaitable[str]]
    has_side_effects: bool          # decides everything below

async def run_side_effect(call: ToolCall, tool: Tool, thread: Thread) -> Message:
    key = idempotency_key(call)                         # same intent -> same key
    if tool.needs_confirmation and not confirmed(thread, call.id):
        thread.append("human_input_requested", tool_call_id=call.id, question=describe(call))
        return PAUSE                                    # resume after the human answers
    thread.append("side_effect_started", tool_call_id=call.id, idempotency_key=key)
    result = await tool.handler(idempotency_key=key, **call.arguments)
    thread.append("side_effect_finished", tool_call_id=call.id, result=result)
    return Message(role="tool", tool_call_id=call.id, content=result)
```

`side_effect_started` 事件在执行前写入。恢复时如果看到它没有对应的 `finished`，运行时知道这个动作状态未知，转交人工，而不是盲目重跑。审计记录就是这两条事件加上触发它们的 `assistant_message`，不需要另建一套日志。

## 对照

- 参考：[12-factor-agents · factor 07 Contact humans with tools](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-07-contact-humans-with-tools.md)（访问日期 2026-09-04）
- 相关课程：[05 Tool Calling](../lessons/05-tool-calling/README.md)（幂等键与确认门的代码）、[07 Agent State 与 Runtime](../lessons/07-agent-state-and-runtime/README.md)（暂停恢复与事件记录）、[19 可靠性、成本、部署与 LLMOps](../lessons/19-reliability-cost-llmops/README.md)（重试策略）

---

[← 原则总览](./README.md)
