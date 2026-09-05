# 17 评测｜练习

## 练习 1：从一个线上失败补案例

假设用户反馈：问「我上周五买的能退吗」，机器人回了退货政策全文，没有回答能不能。给正文的 golden set 加这条案例，写出断言和标签。

验收：v1 在这条上失败（它确实不会处理相对日期），然后你修改 `answer()` 让它通过，且其他 12 条不受影响。

<details><summary>参考答案</summary>

```python
Case("multi-3", "I bought it last Friday, can I still refund?", ("yes", "14 days"), (), ("policy", "multi_step", "relative_date")),
```

新标签 `relative_date` 值得单独开：这类问题的失败原因（日期推理）和其他 policy 问题不同。评测集的标签体系应该随失败模式增长。

</details>

## 练习 2：算一下 kappa 为什么是 0

一个全判 pass 的 judge，一致率 58%、kappa 0.00。不看代码，手算一遍：12 条里人判 pass 7 条，judge 全判 pass。

<details><summary>答案</summary>

观察一致率 = 7/12 = 58%。随机一致的期望 = P(人 pass)·P(judge pass) + P(人 fail)·P(judge fail) = (7/12)(1) + (5/12)(0) = 58%。kappa = (58% − 58%) / (1 − 58%) = 0。

judge 的一致率完全来自"本来就有 58% 该 pass"，它自己没提供任何信息。这就是只报一致率会被骗的原因。

</details>

## 练习 3：给轨迹断言加"顺序"

正文的 `check_trajectory` 检查了工具集合，没检查顺序。加一条断言：`send_email` 如果出现，必须在 `lookup_order` 之后。

验收：构造一个先发邮件再查订单的剧本，断言失败并说明原因。

<details><summary>答案</summary>

```python
names = [n for n, _ in calls]
if "send_email" in names and "lookup_order" in names and names.index("send_email") < names.index("lookup_order"):
    failures.append("emailed before looking up the order")
```

顺序断言在有副作用的工具上尤其重要：先动作再查证，等于用错误信息执行了不可逆操作。

</details>

## 练习 4：基线更新的流程

一个常见实现是「没有基线时自动记一份」。这在真实仓库里是危险的。设计一个基线更新流程，回答：谁能更新、什么时候更新、怎么防止「跑一次就覆盖」。

<details><summary>参考答案</summary>

基线文件进 git，更新它是一次单独的 commit，PR 描述里要写"为什么分数变了"。CI 里的门禁只读基线，永不写。本地想更新基线用显式命令 `--update-baseline`，而且只在当前分数不低于旧基线时允许，低于时要加 `--accept-regression` 并写理由。

这和快照测试（snapshot test）的治理是同一套逻辑。

</details>

## 练习 5：哪些该用断言，哪些该用 judge

对下面五个检查，判断用断言还是 judge，并说一句理由：

1. 回答里不能出现另一个客户的邮箱
2. 回答是否礼貌
3. 回答是否真的回答了用户的问题而不是答非所问
4. 工具调用参数里的 order_id 格式正确
5. 多轮对话里模型是否记住了用户第一轮说的偏好

<details><summary>参考答案</summary>

1. 断言。正则匹配邮箱，排除用户自己的。
2. judge，但先问值不值得测。礼貌很少是产品失败的原因。
3. judge。这是断言写不出来的典型，也是 judge 最容易和人分歧的地方，必须校准。
4. 断言。schema 校验本来就在第 05 课的运行时里，评测只是再确认。
5. 可以是断言：第一轮说"不吃辣"，最后一轮的推荐里不能出现"辣"。能写成断言的尽量写成断言，即使它看起来像语义问题。

</details>
