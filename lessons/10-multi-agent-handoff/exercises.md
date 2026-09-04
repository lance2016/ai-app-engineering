# 10 多智能体、Handoff 与 Racing｜练习

## 练习 1：让专家能把控制权交回来

`01_handoff.py` 只有 triage → billing 一个方向。给 billing 加一个 `transfer_back` 工具，billing 处理完后交回 triage，triage 用一句话收尾。运行时要记录两次交接。

验收：输出里活跃 Agent 的序列是 triage → billing → triage，线程有两条 `handoff` 事件。

<details><summary>提示</summary>

活跃 Agent 是运行时的一个变量，交接工具只是改变它的信号。写一个 `while` 循环：取活跃 Agent、调模型、如果是交接工具就切换并 `continue`，否则输出并结束。注意加步数上限，防止两个 Agent 互相推来推去。

</details>

## 练习 2：三种历史策略的成本和效果

用 `01_handoff.py` 的三种 `HANDOFF_HISTORY`，各构造一个 20 轮的对话历史（前 18 轮闲聊，第 19 轮提到订单号，第 20 轮说被重复扣费），统计专家 Agent 收到的 token 数，并回答：哪种策略让专家丢了订单号？

验收：一张三行表，列是策略、token 数、专家是否知道订单号。

<details><summary>答案</summary>

`full` 知道但最贵；`last` 不知道（订单号在第 19 轮）；`summary` 取决于摘要有没有把订单号带上，`01` 里那个简单的摘要没带。改进 summary 策略的方法是第 08 课的"受保护事实"：交接前从历史里确定性地抽出订单号、金额这类实体，原文附上。

</details>

## 练习 3：给 racing 加上"聊天模型也能调工具"的守卫

`02_racing.py` 里聊天模型只产生文本。改成聊天模型也可能返回工具调用，然后处理这个情况：分类器说"指令"要取消聊天草稿时，如果草稿已经包含工具调用，该怎么办？

验收：写出你的规则并实现。至少要保证同一个动作不会被执行两次。

<details><summary>参考答案</summary>

一种规则：聊天草稿里的工具调用一律丢弃，只执行分类器的裁决。因为聊天模型的工具调用没有经过意图分类，可信度低。另一种规则：两边都产生工具调用时，按工具名去重后执行。第一种更安全，第二种更"聪明"但更难解释。生产里选第一种的多。

</details>

## 练习 4：视图里要不要看到别人的失败

`03_ownership_and_fallback.py` 的 `view_for()` 让 triage 看不到 billing 的失败事件，它只是被运行时用 `fallback_note` 告知了。另一种做法是把 `handoff_failed` 渲染成一条消息放进 triage 的视图。两种做法各有什么后果？

<details><summary>讨论</summary>

放进视图：triage 的模型能"知道"发生了什么，回复更自然，但也可能把内部错误信息（"billing backend unavailable"）原样说给用户。不放进视图、由运行时决定怎么告知：可控，但 triage 的提示词要预留"收到兜底指令时怎么说"的分支。两种都行，关键是内部错误信息在到达用户前必须经过一层过滤，这是第 20 课的内容。

</details>

## 练习 5：读一段事件，判断问题出在哪

```text
user_message        "Cancel my subscription."
assistant/triage    tool_call transfer_to_billing
handoff             triage -> billing
assistant/billing   "Sure, which subscription? I see three on your account."
user_message        "The premium one."
assistant/billing   tool_call transfer_to_triage   (reason: "user wants to cancel")
handoff             billing -> triage
assistant/triage    tool_call transfer_to_billing
handoff             triage -> billing
```

发生了什么？运行时缺了什么？

<details><summary>答案</summary>

两个 Agent 在互相推。billing 收到"取消 premium"后不知道该自己处理，交回 triage；triage 看到取消请求又转给 billing。缺的是运行时的两道守卫：交接次数上限（第 06 课的步数上限在多 Agent 上的形态），以及"刚从 A 交过来的对话不能立刻交回 A"这样的规则。更根本的问题是 billing 的提示词没有说清它负责取消操作，这是 Agent 职责边界的设计问题，运行时守卫只是兜底。

</details>
