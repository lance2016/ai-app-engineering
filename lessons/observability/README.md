---
status: complete
structure: narrative
part: Part 4 生产工程
topic: production-governance
tier: core
estimated_time: 约 30 分钟
---

# 20 可观测性：从日志到 LLM Trace

> 一次回答背后可能有多次模型、工具和检索调用。可观测性的目标是让你能从最终失败回到具体的一跳，而不是多加几行 print。

<details class="case" markdown="1">
<summary>例子：用户说答案错了，日志里只有最后一句模型回复</summary>

没有上下文快照、检索候选和工具结果，就无法判断是数据错、检索漏、模型误读还是工具返回错误。排障只能猜，并且无法复现同一次运行。

!!! note "构造的例子"
    日志缺失用于说明 trace 的最小信息；生产系统还要按隐私和合规要求采样、脱敏。

</details>

## 一次运行应该是一棵树

```text
run
├── model call
├── retrieval
├── tool call
└── model call
```

根 span 关联用户请求和最终状态，子 span 记录模型、检索和工具。每个 span 至少有开始结束时间、状态、错误分类、版本和关联 ID。

## 日志和 Trace 各管什么

| 信息 | 日志 | Trace |
|---|---|---|
| 单条业务事件 | 适合 | 可关联 |
| 跨组件耗时 | 不方便 | 适合 |
| 一次运行的调用树 | 需要自己拼 | 原生表达 |
| 大段用户内容 | 默认不该全记 | 也要脱敏 / 截断 |

Trace 不是把所有输入输出都存下来。密钥、完整个人信息和不必要的原文要屏蔽；大 payload 使用摘要、哈希或受控采样。

## 最小 span 信息

```python
with tracer.span("model.call") as span:
    span.set("model", model_name)
    span.set("prompt_version", prompt_version)
    reply = await adapter.complete(messages)
    span.set("input_tokens", reply.usage.input_tokens)
    span.set("output_tokens", reply.usage.output_tokens)
```

这段代码是机制示意，省略了 tracer 实现和隐私过滤，不能直接运行。异常要同时记录事件和失败状态，否则界面可能显示绿色 span。

## 怎么测

准备一个已知失败的回放样本，检查能否只靠 trace 回答：

- 哪一跳先失败；
- 这次模型看到了哪些上下文版本；
- 检索返回了什么、工具是否真正执行；
- token、耗时、重试和最终终态是什么。

再用故障注入测采样、超时、取消和隐私字段是否仍符合规则。可用“从告警到定位的时间”作为团队指标。

## 参考实现与延伸

参考实现的 trace、结构化日志和故障注入在 [M5 Production](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m5-production)（核对日期 2026-09-10）。属性命名可对照 [OpenTelemetry traces](https://opentelemetry.io/docs/concepts/signals/traces/) 与 [GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)（访问日期 2026-09-10）。

---

[← 上一课 19](../evaluation/README.md) · [下一课 21 →](../reliability-cost-llmops/README.md)
