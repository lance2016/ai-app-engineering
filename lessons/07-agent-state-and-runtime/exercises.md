# 07 Agent State 与 Runtime｜练习

## 练习 1：把崩溃点挪到危险的位置

正文的 `run()` 在 `save()` 之后才可能崩溃，所以恢复是安全的。设想进程崩在 `execute()` 之后、`append("tool_result")` 之前，恢复时会发生什么？

验收：恢复后 `find_restaurants` 被执行了两次（两个进程各一次）。然后解释为什么运行时没法在这里做到"要么都发生要么都不发生"。

<details><summary>答案</summary>

`execute()` 改变的是外部世界，`save()` 改变的是自己的存储，两个系统之间没有事务。这是分布式系统的基本约束，不是代码写得不好。

出路只有两条：让外部系统支持幂等键（第 05 课），或者让工具本身是可以安全重跑的只读操作。对有副作用又不支持幂等键的外部系统，运行时只能在执行前先记一条"即将执行"事件，恢复时看到这条没有对应结果的事件，就知道状态未知，转交人工处理，而不是盲目重跑。

</details>

## 练习 2：用事件推导预算

第 06 课的 `Budget` 是一个单独的对象。改成从线程推导：写一个 `tokens_used(thread)` 函数，要求 `assistant_message` 事件里带上 `usage`，然后把预算检查改成读这个函数。

验收：恢复一个中途暂停的线程时，已经花掉的 token 会被算进去，而不是从零开始。

<details><summary>答案</summary>

在 `append("assistant_message", ...)` 时加 `usage={"in": ..., "out": ...}`，然后：

```python
def tokens_used(thread: Thread) -> int:
    return sum(e.data.get("usage", {}).get("in", 0) + e.data.get("usage", {}).get("out", 0)
               for e in thread.events if e.type == "assistant_message")
```

这正是 factor 05 说的"执行状态是元数据"。预算不需要单独的对象来记，它就在历史里。

</details>

## 练习 3：给事件流加客户端断线重连

正文的事件流假设客户端从头听到尾。真实的浏览器会断线。给 `run_streaming` 加一个 `since: int` 参数，表示客户端已经收到了前几条事件，重连时只补发之后的。

验收：模拟客户端在收到第 3 条后断开，重连时传 `since=3`，只收到后面的事件，且和线程剩余部分一致。

<details><summary>提示</summary>

线程本身就是重放源。重连时先 `yield` `thread.events[since:]` 里已有的事件，再继续正常的循环。不需要另外的消息队列，因为事件已经持久化了。

</details>

## 练习 4：选一个策略并说明理由

三个场景，各选 reject / enqueue / interrupt 中的一个：

1. 用户在语音助手说话时插了一句"算了不用了"
2. 用户在一个正在执行"批量导出 500 份报告"的任务中途发了"顺便也导出上个月的"
3. 用户在支付确认页连点了两次"确认"

<details><summary>参考答案</summary>

1. interrupt。用户明确改主意了，继续说完是浪费，而且体验差。保留已完成的工具结果。
2. enqueue。第一个任务有价值且不可逆地花了资源，第二个请求是追加不是替代。
3. reject。第二次点击是同一个意图的重复，接受它会变成两笔支付。这里 reject 和第 05 课的幂等键是同一件事的两个层面。

没有一个策略适合所有场景，所以它必须是运行时的显式参数，而不是框架默认值。

</details>

## 练习 5：从 status() 的实现找一个 bug

看正文里 `status()` 的推导规则。构造一个事件序列，让它返回错误的状态。

<details><summary>答案</summary>

`human_input_requested` 之后如果模型又被调用并直接回答了（比如运行时代码有 bug，没有等 `human_input` 就继续了），事件序列是 `... human_input_requested, assistant_message, run_finished`，`status()` 返回 `finished`，掩盖了"没等用户就自己做决定"的问题。

修法不在 `status()` 里，而是在 `run()` 里：`pending_tool_calls()` 里有 `request_human_input` 时不允许调模型。推导函数只能忠实反映事件，事件的合法顺序要由写入方保证。这也是为什么换成数据库时光加一张表不够，还要给写入加约束。

</details>
