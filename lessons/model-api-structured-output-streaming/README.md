---
status: complete
structure: narrative
part: Part 1 模型与上下文
topic: model-interface
tier: core
estimated_time: 约 35 分钟
---

# 02 模型调用、结构化输出与流式

> 调用层的任务不是把 SDK 包起来，而是把供应商的消息、事件和错误翻译成应用能校验的边界。

<details class="case" markdown="1">
<summary>例子：页面已经显示了半句答案，但工具参数还没有收完整</summary>

流式响应同时包含文本增量和工具参数增量。页面可以立即显示文本，但工具参数必须拼完整、解析成功并通过权限检查后才能执行。把每个 chunk 都当成完整结果，会把半个 JSON 交给工具。

!!! note "构造的例子"
    事件顺序和字段是为说明流式边界构造的；真实事件名称以供应商文档为准。

</details>

## 一次调用要保住六件事

应用层只需要稳定地处理：消息、工具定义、输出文本、工具调用、用量、错误。供应商可以改变字段名，但这六类信息不能在适配器里悄悄丢掉。

| 输入 | 输出 | 运行时责任 |
|---|---|---|
| 消息与指令 | 文本增量 | 拼接并标记结束 |
| 工具 schema | 完整工具调用 | 缓冲、解析、校验 |
| 模型与参数 | usage / error | 归一化、计费、分类 |

结构化输出不是“模型保证 JSON”。它最多减少格式错误；schema 校验、缺字段处理和业务规则仍由代码负责。

## 结构化输出的三层守卫

1. **语法层**：能否解析 JSON。
2. **结构层**：是否符合 schema。
3. **业务层**：金额、权限、状态等规则是否成立。

```python
raw = await adapter.complete(messages, response_format=OrderSchema)
data = parse_json(raw)
order = OrderSchema.model_validate(data)
assert order.amount <= context.max_amount
```

这段代码是机制示意，省略了供应商 SDK 和错误类型，不能直接运行。三层失败要记录不同原因，否则评测只会得到一个模糊的“解析失败”。

## 流式只改变展示时机

流式响应把完整结果拆成事件，不改变最终的校验边界：

```text
text_delta       → 可以边到边显示
tool_delta       → 只能先缓冲
tool_finished    → 解析、校验后才能执行
stream_error     → 结束当前输出并返回可恢复错误
```

文本可以渐进展示；命令、SQL、付款参数和结构化对象必须等完整结果。连接断开时，客户端还要知道输出是完成、取消还是失败。

## 重试看错误类型

超时、限流和临时网络错误可能重试；参数错误、权限拒绝和业务冲突不应盲目重试。重试次数不是安全策略，预算、幂等键和错误分类才是。

## 怎么测

建立一组固定回放样本，覆盖：完整文本、分块文本、分块 JSON、字段缺失、业务规则失败、流中断和重复事件。记录：

- 结构化解析率和业务校验率；
- 首 token 延迟与完整响应延迟；
- 工具调用是否只在完整参数通过校验后发生；
- 每类错误的重试次数。

## 参考实现与延伸

参考实现的统一 adapter、SSE 增量和错误归一化在 [M1 API 骨架](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m1-api-skeleton)（核对日期 2026-09-10）。字段细节查[模型接口参考](../../reference/model-interfaces.md)。

可对照 [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat) 与 [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages)（访问日期 2026-09-10）。

---

[← 上一课 01](../how-llms-work/README.md) · [下一课 03 →](../prompt-engineering/README.md)
