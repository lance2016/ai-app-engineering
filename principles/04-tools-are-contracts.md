---
status: complete
---

# 原则 04｜Tool 就是带契约的结构化输出

> 一个工具对模型来说是一段 JSON Schema，对运行时来说是一个有明确输入、输出和副作用声明的函数。两边都是契约，缺一边都会出问题。

## 主张

工具调用就是模型输出一段结构化 JSON，确定性代码照着它做事。所以设计工具就是设计契约，契约有四部分：

1. **名字和描述**：模型靠它决定何时用这个工具。描述写的是「什么时候该用」，不是实现细节。
2. **参数 schema**：模型靠它填参数，运行时靠它校验。同一份 schema，两边共用。
3. **结果形状**：成功返回什么、失败返回什么。失败也是结果，不是异常。
4. **副作用声明**：只读还是会改变外部世界。这决定它要不要走确认门、要不要幂等键、能不能并行。

契约之外的东西不该由工具承担。工具不判断权限，不做重试策略，不管上下文放不放得下。那些是运行时的事。

## 违反它会怎样

- **描述写成了实现说明。** 「调用内部 API v2 的 /search 接口」对模型没有任何帮助；「当用户问到公司政策、流程或历史文档时使用」才是模型需要的。
- **结果是一段自由文本。** 工具返回 `"Error: connection refused"` 和返回 `"connection refused is a common error..."` 对模型来说长得一样。没有 `is_error` 标记，模型会把错误信息当成正常内容往下编。
- **副作用没有声明。** 一个叫 `check_order` 的工具顺手把订单标成了「已查看」。运行时以为它只读，在重试和并行时调了三次。
- **把异常抛给模型。** 工具执行抛出 Python 异常，整个 Agent 循环崩掉，用户看到 500。模型本来有机会换个办法或者告诉用户「暂时查不到」。

## 最小做法

```python
@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str          # when to use it, written for the model
    parameters: dict          # JSON Schema; also used for validation

@dataclass(frozen=True)
class Tool:
    spec: ToolSpec
    handler: Callable[[dict], str]
    has_side_effects: bool    # drives confirmation, idempotency, parallelism

def result(call, content, *, is_error=False) -> Message:
    return Message(role="tool", tool_call_id=call.id, content=content, is_error=is_error)
```

用 Pydantic 模型生成 `parameters`，校验时用同一个模型，schema 就永远不会和校验逻辑漂移。

## 对照

- 参考：[12-factor-agents · factor 04](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-04-tools-are-structured-outputs.md)（访问日期 2026-09-04）；[Anthropic · Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)（访问日期 2026-09-04），看 `input_schema` 和 `tool_result` 的 `is_error` 字段
- 相关课程：[05 Tool Calling](../lessons/tool-calling/README.md)、[11 MCP](../lessons/mcp/README.md)

---

[← 原则总览](./README.md)
