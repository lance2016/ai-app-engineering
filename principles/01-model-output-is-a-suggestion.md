---
status: complete
---

# 原则 01｜模型输出是建议，不是执行结果

> 模型说「我调用了 `delete_doc`」，什么都还没发生。模型说「已经删除」，也什么都没发生。只有运行时执行过的动作才算发生过。

## 主张

模型的输出只有一种身份：**一段结构化的建议**。它建议下一步调用哪个工具、传什么参数、或者回什么话。把这个建议变成事实的是运行时里的确定性代码：查注册表、校验参数、检查权限、执行、记录结果。

这条原则决定了责任边界。模型负责「想做什么」，代码负责「能不能做、怎么做、做成了没有」。任何一个环节交给模型自己判断，系统就多了一个不可审计的决策点。

## 违反它会怎样

三种常见形态，都在真实系统里出现过：

- **执行了不存在的工具。** 意图分类模型输出了一个训练时见过、但当前请求没有注册的工具名。运行时没有查表，直接按名字反射调用，抛了一个和用户毫无关系的异常。
- **把文本当成动作。** 聊天模型在正文里写了一段 `{"function": "set_volume", "args": {...}}`，运行时用正则把它捞出来执行了。模型只是在「表演」调用工具，它的训练数据里有太多这种格式。
- **把「我做了」当成「做了」。** 工具调用超时没有拿到结果，模型在下一轮直接对用户说「已经帮你转账了」。用户信了，账没动。

三种错误的根源相同：运行时把模型输出当成了事实来源。

## 最小做法

只从工具调用通道取动作，只执行注册表里有的工具，把每一步的真实结果回喂给模型：

```python
reply = await model.complete(messages, tools=registry.specs(allowlist))
for call in reply.tool_calls:                  # never parse actions out of reply.content
    tool = registry.get(call.name)             # None -> error result, not an exception
    if tool is None:
        result = error_result(call, f"unknown tool: {call.name}")
    else:
        result = await tool.run(call)          # validate, authorize, execute, record
    messages.append(result)                    # the model sees what really happened
```

用户看到的「已完成」，必须来自 `result`，不能来自模型的下一句话。

## 对照

- 参考：[12-factor-agents · factor 01](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-01-natural-language-to-tool-calls.md)、[factor 04](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-04-tools-are-structured-outputs.md)（访问日期 2026-09-04）
- 相关课程：[05 Tool Calling](../lessons/tool-calling/README.md)、[06 Agent 循环与控制流](../lessons/agent-loop/README.md)

---

[← 原则总览](./README.md)
