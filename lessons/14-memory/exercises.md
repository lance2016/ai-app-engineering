# 14 Memory｜练习

## 练习 1：让来源可以被验证

正文的提取存下了 `source_event_ids`，但没有检查这些编号指向的事件里是否真的包含那条记忆的依据。加一个校验：记忆 `content` 里的关键词至少要在某个来源事件的文本里出现，否则标记为 `unverified`。

验收：把某条记忆的 `source_event_ids` 改成指向一条不相关的 assistant 消息，运行后这条被标记，其余正常。

<details><summary>提示</summary>

不要追求精确匹配，提取器会改写措辞。取 `content` 里长度大于 3 的词，看有没有任何一个出现在来源文本里。这是弱校验，目的是抓"编号乱填"，不是抓语义偏差。

</details>

## 练习 2：整合时保留冲突的证据

正文里冲突的旧记忆进了 `history`，带 `superseded_by`。加一个 `explain(subject)` 函数，输出这个主题的完整变化链：什么时候说了什么、被什么替换。

验收：`explain("diet")` 输出两行，按时间排序，能看出从"素食"到"开始吃鱼"的变化和各自的来源事件。

<details><summary>答案</summary>

```python
def explain(self, subject: str) -> list[str]:
    chain = [m for m in self.history + self.active if m.subject == subject]
    chain.sort(key=lambda m: m.observed_on)
    return [f"{m.observed_on}: {m.content!r} <- events {m.source_event_ids}" + (f" (superseded by {m.superseded_by!r})" if m.superseded_by else "") for m in chain]
```

这个函数就是用户问"你为什么觉得我不吃素了"时，助手应该给出的回答的数据来源。

</details>

## 练习 3：按来源线程删除

正文的 `forget()` 按 `subject` 删。用户有时会说「忘掉我们上周那次对话里说的所有事」。实现 `forget_thread(memories, user_id, thread_id)`。

验收：删除 `thr_u42_01` 后，`m1` 和 `m2` 都没了，`m3`（来自另一个线程）保留，审计里记录了两条被删记忆的 id 和来源。

<details><summary>答案</summary>

过滤条件从 `m.subject == subject` 改成 `m.source_thread == thread_id`。这题的意义在于：来源不只是为了解释，它是删除操作的索引。没有 `source_thread` 字段，这个需求实现不了。

</details>

## 练习 4：热路径还是后台

三个场景，各选热路径提取或后台提取，说理由：

1. 用户说"记住，我以后都要无糖的"
2. 一次 40 轮的旅行规划对话结束了
3. 客服 Agent 每天处理上万次对话

<details><summary>参考答案</summary>

1. 热路径。用户明确要求记住，下一句就可能用到，延迟不可接受。
2. 后台。对话结束后批量提取一次，比每轮都提取省 39 次调用，而且结束时信息最全，整合最容易。
3. 后台，而且要抽样。上万次对话全提取成本高，大多数对话没有值得跨会话记住的东西。可以先用便宜的规则或小模型判断"这次对话有没有长期记忆价值"，有的才进提取。

</details>

## 练习 5：找出租户泄漏的另一条路径

`03` 的 `retrieve()` 按 `user_id` 过滤了。假设检索是正确的，还有哪一步可能把 `u99` 的记忆泄漏给 `u42`？

<details><summary>答案</summary>

提取这一步。如果一个线程里有多个用户（家庭共用设备、群聊、客服转接），提取器从线程里抽出的记忆会被记到"当前用户"名下，实际上是别人说的。所以提取时每条候选记忆的来源事件要能对应到说话人，写入时按说话人而不是按线程归属。检索过滤是最后一道防线，不是唯一一道。

</details>
