---
status: complete
structure: narrative
part: Part 2 Tool 与 Agent
topic: runtime
tier: core
estimated_time: 约 35 分钟
---

# 05 Tool Calling：从建议到副作用

> Tool Calling 的核心不是让模型“会调用函数”，而是把模型的建议放进一条可校验、可授权、可恢复的执行链。

<details class="case" markdown="1">
<summary>例子：模型请求退款，重试后用户收到两次退款</summary>

第一次请求可能已经成功，但响应在网络中丢失。运行时只看到超时，于是再次执行。没有幂等键时，外部系统把两次请求当成两笔退款。

!!! note "构造的例子"
    事故链用于说明“执行成功”和“拿到结果”不是一回事；金额和接口形状不代表真实项目记录。

</details>

## 一次 Tool Calling 的边界

```text
模型提出工具名和参数
        ↓
运行时查注册表、校验 schema、绑定身份
        ↓
权限 / 风险 / 确认 / 幂等检查
        ↓
工具执行，记录结果，再回传给模型
```

模型负责提出意图，运行时负责决定能不能做。工具结果是观察，不是模型可以自行改写的事实。

## Tool 契约至少有四部分

| 部分 | 解决什么问题 |
|---|---|
| 名字和描述 | 模型什么时候应该提出调用 |
| 参数 schema | 模型如何填，代码如何校验 |
| 成功 / 失败结果 | 下一轮如何继续或换路 |
| 副作用声明 | 是否确认、幂等、串行和审计 |

白名单和权限不能只写在 Prompt 里。Prompt 可以减少误用，代码才是最后一道边界。

## 最小守卫顺序

```python
call = model_reply.tool_call
tool = registry.get(call.name)
args = schema.validate(call.arguments)
identity = runtime_context.identity

if tool is None or not policy.allows(identity, tool, args):
    return error_result(call, "tool is not allowed")
if tool.has_side_effects and not confirmation.exists(call):
    return pause_for_human(call)
return execute_once(tool, args, idempotency_key(call, identity))
```

这段代码只说明顺序，省略了异常类型、存储和异步细节，不能直接运行。拒绝、参数错误、临时失败和未知结果要分开记录。

## 幂等不是“多跑几次就没事”

优先让外部接口接受业务幂等键。只有 `tool_call.id` 只能防同一次调用的重试，防不了模型下一轮重新表达同一业务意图。外部接口不支持幂等时，要查询状态、进入对账队列或交给人工，不要盲目重跑。

## 怎么测

用一组固定工具调用回放：未知工具、坏参数、越租户、需要确认、超时后重试、执行成功但响应丢失。检查：

- 未授权调用是否零执行；
- 相同业务意图是否只产生一次外部效果；
- 错误是否能回喂而不让循环直接 500；
- 每个副作用是否留下参数、身份、确认和结果。

## 参考实现与延伸

参考实现的注册表、守卫和执行器在 [M3 Tool Workflow](https://github.com/lance2016/ai-app-engineering-ref/tree/main/project/m3-tool-workflow)（核对日期 2026-09-10）。工具协议的 `tool_result` 形状可对照 [Anthropic Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)（访问日期 2026-09-10）。

---

[← 上一课 04](../embeddings-and-vector-search/README.md) · [下一课 06 →](../agent-loop/README.md)
