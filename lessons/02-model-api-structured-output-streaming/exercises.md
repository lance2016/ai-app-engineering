# 02 模型调用、结构化输出与流式｜练习

## 练习 1：给 schema 加一个业务约束

在 `02_structured_output.py` 的 `Invoice` 里加一个校验：`total` 必须大于 0，`currency` 必须是大写。然后在 `BAD` 里放一个 `"currency": "eur"`，跑 `INJECT_BAD_JSON=1`。

验收：第一次校验错误的原文里出现你新加的约束描述，第二次通过。你没有写任何"把小写转大写"的代码。

<details><summary>提示与答案</summary>

`total: float = Field(gt=0)`；currency 用 `field_validator` 检查 `v.isupper()`，不满足就 `raise ValueError("currency must be upper-case ISO code")`。

关键点在最后一句验收：修正是模型做的，运行时只判对错。如果你忍不住写了 `.upper()`，问自己下次模型返回 "Euro" 怎么办。

</details>

## 练习 2：两个消费者读一条流

改 `03_streaming.py`：把消费逻辑拆成两个函数，`ui_consumer` 每收到含句号的 delta 就打印一整句，`tool_consumer` 只在 `done=True` 时打印工具调用。让 fake 的剧本改成一个带工具调用的响应（用 `tool_call_response`）。

验收：文本部分（如果有）按句输出，工具名只在最后打印一次，两个消费者互不知道对方存在。

<details><summary>答案</summary>

`tool_call_response` 生成的响应 `content` 为空，所以流里只有一个 `done` chunk。想同时看到文本和工具调用，构造 `ModelResponse(content="Let me check.", tool_calls=(ToolCall(...),))`。

结构上，把 `async for chunk in model.stream(...)` 放在一个地方，每个 chunk 分发给两个消费者函数。这就是第 07 课事件流的雏形：一份数据，多个视图。

</details>

## 练习 3：让重试知道时间

`04_retry_and_cost.py` 的重试只数次数。给 `complete_with_retry` 加一个 `deadline_seconds` 参数，总耗时超过它就放弃，哪怕次数没用完。

验收：`INJECT_RATE_LIMIT=1` 时把 `deadline_seconds` 设成 0.08，应该在第二次重试前放弃并抛出原始的 `RateLimited`。

<details><summary>答案</summary>

进入函数时记 `started = time.monotonic()`，每次准备 `sleep(delay)` 前检查 `time.monotonic() - started + delay > deadline_seconds`，超了就 `raise`。

为什么要这个：面向用户的请求有一个用户能忍的上限，次数限制不知道这件事。第 06 课的时间预算和第 19 课的超时策略都建立在这一条上。

</details>

## 练习 4：读一段账单，找出异常

下面是某个功能一天的成本账本摘要：

```text
calls=12000  input_tokens=38,400,000  output_tokens=960,000
avg input per call = 3200   avg output per call = 80
```

平均每次调用输入 3200 token、输出 80 token。这个功能是一个"把用户一句话分类到三个标签之一"的接口。哪里不对？你会先查什么？

<details><summary>答案</summary>

分类一句话，输出 80 token 偏多但还算合理（模型可能在解释）；输入 3200 token 完全不合理，一句话加一段指令不该超过几百。最可能的原因是每次调用都把整段对话历史带上了，或者系统提示里塞了不必要的示例和工具定义。

先查一次真实请求的完整消息列表（第 08 课会讲怎么让这个随时可见），再查 `max_tokens` 有没有设。这题的重点是：账本存在的意义就是让这种问题在账单到期前被看见。

</details>

## 练习 5：真模型上验证一个假设

需要 key。用 `05_real_params_probe.py` 的写法，在 temperature 0 下把同一个抽取任务跑 5 次，比较返回是否完全一致。

验收：写下你观察到的结果，以及它是否支持"temperature 0 等于确定性"这个说法。

<details><summary>参考答案</summary>

大多数供应商在 temperature 0 下输出高度一致但不保证逐字节相同，批处理、浮点误差、模型版本静默更新都可能让结果有微小差异。所以评测（第 17 课）不能只靠 temperature 0 来消除方差，还是要多跑几次看分布。

</details>
