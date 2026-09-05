# 08 Agent 的 Context Engineering｜练习

## 练习 1：按轮裁剪而不是按条

正文的 `build()` 从最近往前逐条保留历史，可能在一轮中间切断：保留了 assistant 的回答却丢了它回答的那个问题。改成按「一问一答」成对裁剪。

验收标准：历史被裁剪时，保留下来的第一条永远是 `user`。

<details><summary>答案</summary>

把 `history` 先按 user 消息切成若干轮（每轮从一条 user 开始，到下一条 user 之前结束），然后对轮做和现在一样的逆序填充。工具调用多的轮会比较大，一个轮放不下就整轮丢，不要拆开。

</details>

## 练习 2：把受保护事实的提取交给模型，再评估

正文的 `extract_protected` 是关键词匹配。改成用一次模型调用抽取「用户明确表达的约束」，然后设计一个包含五段对话的小测试集，比较关键词版和模型版各漏了什么。

验收：写出一张表，行是五段对话，列是两种方法各提取到的约束，标出漏抽和误抽。

<details><summary>讨论</summary>

模型版能抓到"我不吃辣"这种没有关键词的表达，但也可能把"朋友不吃辣"误当成用户约束。这一题没有正确答案，目的是让你体会：一旦把确定性逻辑换成模型，就必须配一个评测集。这是第 17 课的主题。

</details>

## 练习 3：给 shape() 加"按需展开"的第二级

正文的 `fetch_rows` 按偏移取行。加一个 `describe_column(result_id, column)`，返回该列的去重值和计数，让模型能先看分布再决定取哪些行。

验收：模型调用 `describe_column(res, "status")` 得到 `{"shipped": 167, "pending": 167, "refunded": 166}`，不需要拉任何整行。

<details><summary>提示</summary>

`RESULT_STORE` 里有完整数据，聚合在运行时做。这正是 Anthropic 说的"模型写针对性的查询，不把整个数据对象加载进上下文"。

</details>

## 练习 4：找出你自己项目里的易变前缀

不写代码。打开你正在用的任何一个 LLM 应用的系统提示词，找出所有每次请求都会变的内容（时间、用户名、会话 id、随机示例）。回答：哪些可以挪到最后一条消息，哪些必须留在前面，为什么？

<details><summary>参考答案</summary>

时间、位置、设备状态几乎都能挪到最后。用户名如果影响模型的称呼方式，可以留在前面但整个会话不变，不影响缓存。真正必须在前面且每次不同的东西很少；如果找到了，问一句"模型真的需要在指令层面知道它吗，还是放在输入里就够了"。

</details>

## 练习 5：读一段窗口，判断哪个区段出了问题

```text
system     ~600 tokens  "You are a support assistant..."
reference  ~3000 tokens  <doc id=0> ... <doc id=7>
summary    ~400 tokens  "User has asked about shipping, returns..."
user       "Where is my order?"
assistant  "According to doc 3, returns take 14 days."
```

用户问的是订单在哪，模型答了退货政策。你会先查哪个区段？

<details><summary>答案</summary>

先查 reference。八篇文档 3000 token 里可能根本没有订单状态相关的内容（那需要调一个工具，不是查文档），模型在一堆退货文档里"找到"了最接近的东西。这是 distraction：资料太多且不相关，模型被它带走。修法是检索时按问题过滤文档数量，以及让"查订单"有对应的工具而不是靠文档。第二个要查的是 summary 有没有把"用户之前问过退货"这件事强化到模型以为这次也是退货。

</details>
