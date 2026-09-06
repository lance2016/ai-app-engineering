# 05 Tool Calling｜练习

> 前三题动手，后两题思考。每题先自己做，再看答案。

## 练习 1：给校验加一个字段

给正文的 `GetWeatherArgs` 加一个 `date: datetime.date` 字段，然后设想模型返回了 `"date": "yesterday"`。

验收：写出这时的消息序列——一条 `[ERROR] invalid arguments: ...` 的工具结果，模型换成合法日期重新调用，最后正常回答。

<details><summary>提示与答案</summary>

Pydantic 会把 `"2026-09-04"` 解析成 `date`，把 `"yesterday"` 报成 `Input should be a valid date`。剧本要改成三步：坏调用、好调用、最终回答。

关键点：你没有写任何日期解析代码，schema 和校验用的是同一个模型，这就是原则 04 说的"契约两边共用"。

</details>

## 练习 2：按角色的白名单

把正文里写死的白名单改成一个函数 `allowlist_for(role: str) -> frozenset[str]`：`"viewer"` 只能 `search_docs`，`"editor"` 可以 `search_docs` 和 `delete_doc`。写出两个角色下模型分别看到什么、能调什么。

验收：viewer 调 `delete_doc` 时拿到 `tool not allowed here` 的错误结果；editor 能正常删除。并且 viewer 的请求里，`registry.specs()` 返回的列表根本不包含 `delete_doc`。

<details><summary>答案</summary>

```python
ROLE_TOOLS = {"viewer": frozenset({"search_docs"}), "editor": frozenset({"search_docs", "delete_doc"})}

def allowlist_for(role: str) -> frozenset[str]:
    return ROLE_TOOLS.get(role, frozenset())
```

第二条验收才是重点：白名单要在"告诉模型有什么工具"时就生效。`dispatch` 里的检查是第二道防线，防的是模型编造名字，不是主要手段。

</details>

## 练习 3：只做第一层会漏掉什么

系统只实现了正文的 `retry_key`。跑出这样一段记录：模型发起转账（`call_a1`）→ 超时 → 重试同一个 `call_a1` → 仍然超时 → 运行时返回"状态未知" → 模型在下一轮重新发起同一笔转账，拿到新 id `call_7f3b`。

账本里最终有几笔？把每一步的键写出来。

<details><summary>答案</summary>

**两笔。** `call_a1` 的两次尝试共用 `toolcall:call_a1`，银行识别为重放，只记一笔；下一轮的 `call_7f3b` 派生出 `toolcall:call_7f3b`，是个全新的键，银行认为这是第二笔业务。

第一层做的事完全正确——它防的就是"同一次调用重试不能变两笔"。漏掉的是另一件事：**模型重新发起同一个意图**。补上 `business_key` 之后，只要 `confirmation_id` 还是用户那一次确认，两轮就会撞上同一个键。

这里有个容易搞反的点：`business_key` **不能**只用工具名加参数。用户真的想连转两笔 750 给同一个人时，参数完全一样，第二笔会被误判成重放。所以键里必须有一个能区分"两次不同意图"的东西——用户确认 id、订单号、审批单号都行，**但不能是模型生成的 id**，因为那个每轮都在变。

</details>

## 练习 4：确认门超时怎么办

正文的 `ask_user` 是同步等答案的。真实系统里用户可能十分钟不回。这段时间里 Agent 循环该做什么？三个方案里选一个并说理由：一直等、超时后视为拒绝、超时后把整个任务挂起。

<details><summary>答案</summary>

一直等会占着连接和内存，用户一多就撑不住。超时视为拒绝最简单，但用户回来发现任务莫名结束了会困惑。挂起是正确方向：把"等待确认"作为一个可以持久化的状态存下来，释放所有资源，用户回来时从这个状态恢复。

这就是第 07 课 State 与 Runtime 要解决的问题。这一课的 `ask_user` 故意写成最简单的形态，让你先看到需求。

</details>

## 练习 5：读一段记录，判断失败在哪一层

下面是一段调用记录，用户问"帮我把上周的会议纪要发给张三"：

```text
assistant: ToolCall(name="send_email", arguments={"to": "zhangsan", "subject": "会议纪要"})
tool [ok]: {"status": "queued", "message_id": "m_881"}
assistant: 已经发给张三了。
```

用户随后反馈没收到。失败发生在三件事的哪一层？你会先查什么？

<details><summary>答案</summary>

从记录看，选工具正确（`send_email`），参数通过了校验（没有 error），外部系统返回了 `queued`。所以问题最可能在第三层"外部系统真的完成了吗"：`queued` 不等于 `delivered`，而且 `"to": "zhangsan"` 不是邮箱地址，校验可能只检查了类型是字符串。

先查两件事：`m_881` 在邮件系统里的真实状态；`send_email` 的 schema 是否把 `to` 约束成了邮箱格式。第二个问题说明 schema 校验通过不等于参数语义正确，这是校验能力的边界。

</details>
