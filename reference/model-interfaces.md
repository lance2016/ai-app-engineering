---
status: complete
---

# 模型接口参考：三套调用形状怎么对齐

> 这是查表页，不是主线课程。先读 [00 起步](../lessons/setup/README.md) 建立边界，再回来查具体字段。

## 三套接口的最小映射

| 项目 | Chat Completions | Responses | Claude Messages |
|---|---|---|---|
| 请求入口 | `POST /v1/chat/completions` | `POST /v1/responses` | `POST /v1/messages` |
| 普通输入 | `messages` | `input` | `messages` |
| 系统指令 | `role="system"` 消息 | 顶层 `instructions` | 顶层 `system` |
| 普通文本输出 | `choices[0].message.content` | `output_text` | `content` 中的 text block |
| 工具定义 | `function` 再嵌一层 | `name`、`parameters` 平铺 | `name`、`input_schema` |
| 工具调用 ID | `tool_call_id` | `call_id` | `tool_use_id` |
| 工具结果角色 | `role="tool"` | `function_call_output` 条目 | `role="user"` 中的 `tool_result` |
| 输出上限 | `max_completion_tokens` | `max_output_tokens` | `max_tokens`，通常必填 |

表格只描述常见形状，不代表兼容服务完整实现了对应语义。兼容接口可能接受字段但忽略它，尤其是服务端会话状态和内置工具。

## 三个最容易错的地方

### 1. 工具调用不是执行结果

三家接口都把工具调用表示成模型输出的一部分。应用必须自己完成：

1. 读取工具名和参数。
2. 校验 schema 和业务权限。
3. 执行工具或进入人工确认。
4. 按对应接口的形状回传结果。

模型回复“已经完成”不能证明动作发生过。

### 2. Claude 的工具结果属于 user 消息

Claude 的消息角色主要是 `user` 和 `assistant`。工具结果示意如下，省略初始化和错误处理：

```python
messages.append({"role": "assistant", "content": response.content})
messages.append({"role": "user", "content": [{
    "type": "tool_result",
    "tool_use_id": tool_use.id,
    "content": json.dumps(result),
}]})
```

这里的 `user` 只表示“外部信息进入上下文”，不表示用户亲自输入了这段内容。适配器要保留这种语义，不要把它翻译成 `role="tool"` 后直接发给 Claude。

### 3. Responses 的状态语义不能想当然

`previous_response_id` 可以减少应用重发历史的工作，但是否保存、保存多久、哪些内容可以继续引用，要看具体服务。兼容服务可能只支持字段形状，不支持同样的服务端状态。

需要精细控制上下文、审计每一轮输入，或者跨供应商运行时，仍然应该由应用保存事件和消息历史。

## 选型的最小判断

| 需求 | 优先考虑 |
|---|---|
| 跨多家 OpenAI 兼容服务 | Chat Completions 形状，加自己的 adapter |
| 只用 OpenAI 并依赖内置工具或响应续接 | Responses，但核对状态语义 |
| 使用 Claude 原生能力 | Messages，加 Claude adapter |
| 需要可控历史、fake 测试和审计 | 应用自己保存状态，不依赖服务端会话 |

这不是永久的产品推荐。模型、字段和价格会变，上线前要重新核对官方文档和自己的评测集。

## 官方资料

- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)（访问日期 2026-09-10）
- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)（访问日期 2026-09-10）
- [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages)（访问日期 2026-09-10）
- [Anthropic Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)（访问日期 2026-09-10）
- [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/)（访问日期 2026-09-10）
