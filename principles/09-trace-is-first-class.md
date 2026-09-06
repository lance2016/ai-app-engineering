---
status: complete
---

# 原则 09｜Trace 是一等公民，第一次调用就该有

> 一个 Agent 的一次回答背后是五次模型调用、三次工具调用和两次检索。没有 trace，你看到的只有最后那句话。出问题时，你在猜；没出问题时，你不知道它花了多少钱。

## 主张

Trace 是一棵 span 树：根是一次运行，子节点是每次模型调用、工具调用、检索。每个 span 带名字、属性、耗时、状态。它不是排障时才加的东西，而是运行时的一部分，理由有三：

1. **它是原则 07 的前提。** 分层定位失败要看每一层的输入输出，这些数据只有 trace 里有。事后加是加不回来的。
2. **它是评测的数据来源。** 原则 08 的评测集从哪来？从 trace 里挑真实失败的运行。轨迹评测、录制回放，都是对 trace 做断言。
3. **它是成本的账本。** token 用量在每个 chat span 上，加起来就是这次运行的成本。没有 trace，成本只有月底账单一个数字。

两条实践规则：

- **属性名用 OpenTelemetry GenAI 语义约定。** `gen_ai.provider.name`、`gen_ai.request.model`、`gen_ai.usage.input_tokens`、`gen_ai.tool.name`。用标准名字，Phoenix、Langfuse、任何 collector 都直接认；自己起名，换一个后端就要重做。注意 `gen_ai.system` 和 `gen_ai.usage.prompt_tokens` 已经废弃，官方的 GenAI 约定 2026 年迁到了独立仓库。
- **出错时 `record_exception` 和 `set_status(ERROR)` 一起调。** 前者只是在 span 上加一个事件，后者才改状态。只调前者，UI 里这个 span 是绿的，异常藏在事件列表里，没人会点开看。

## 违反它会怎样

- **排障靠加 print。** 线上一个回答错了，工程师在本地复现，加二十个 print，复现不出来，因为线上那次的检索结果和本地不一样。有 trace 的话，那次运行的每一层输入输出都在。
- **成本异常一个月后才知道。** 某个工具偶尔返回超大结果，下一轮 input token 暴涨十倍。没有 per-run 的 token 属性，只有账单在涨。
- **异常被记录了，没人看见。** 作者的项目里踩过：`span.record_exception(e)` 写了，`set_status` 没写，Phoenix 里所有 span 都是绿色的，一批工具超时静默了两周。
- **每个后端一套属性名。** 先用 LangSmith 的字段名，换 Phoenix 时全改一遍，改完发现两个月的历史数据对不上。

## 最小做法

```python
with tracer.span(f"chat {provider}", **{
    "gen_ai.operation.name": "chat",
    "gen_ai.provider.name": provider,
    "gen_ai.request.model": model_name,
}) as span:
    reply = await adapter.complete(messages, tools)
    span.set_attribute("gen_ai.usage.input_tokens", reply.usage.input_tokens)
    span.set_attribute("gen_ai.usage.output_tokens", reply.usage.output_tokens)

with tracer.span(f"execute_tool {call.name}", **{"gen_ai.tool.name": call.name}) as span:
    try:
        result = await run_tool(call)
    except Exception as exc:
        span.record_exception(exc)
        span.set_status("ERROR", str(exc))   # both, always
        raise
```

`tracer` 可以是 OpenTelemetry SDK，也可以是第 19 课里五十行的自制版。属性名不变，后端随时换。

## 对照

- 参考：[OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)（访问日期 2026-09-04），`docs/gen-ai/gen-ai-spans.md` 与 `gen-ai-agent-spans.md`；[OpenTelemetry 属性注册表 · gen_ai](https://github.com/open-telemetry/semantic-conventions/blob/main/docs/registry/attributes/gen-ai.md)（访问日期 2026-09-04），看哪些名字已标 deprecated；[Arize Phoenix](https://github.com/Arize-ai/phoenix) 与 [Langfuse](https://github.com/langfuse/langfuse)（访问日期 2026-09-04），两者都基于 OpenTelemetry 接入
- 相关课程：[19 可观测性](../lessons/19-observability/README.md)

---

[← 原则总览](./README.md)
