---
status: complete
---

# 原则 03｜Prompt 和 Context Window 必须自己掌控，不交给框架黑盒

> 模型是无状态函数，输出的质量取决于输入。如果你看不到、改不了发给模型的每一个字节，你就没有在做工程，只是在祈祷。

## 主张

两件东西必须在你自己的代码里，而不是框架的某个默认值里：

1. **Prompt**：系统指令、示例、输出格式要求。它们是代码，要进版本控制、要能 diff、要能针对它们写评测。
2. **Context window 的组装逻辑**：每一轮哪些历史进去、检索结果放在哪、工具结果怎么整形、什么时候压缩。这个逻辑决定了模型每次"看到什么"，它比任何单条提示词都重要。

12-factor-agents 把这两条分别列为 factor 02 和 factor 03，并且指出你甚至不必用标准的 system / user / assistant 消息格式：把整段历史打包成一条消息、用自定义的结构化格式，往往更省 token、更集中注意力。要不要这么做另说，但你得有这个自由。

Anthropic 把这叫 context engineering，并给了一个约束：上下文是有限的 attention budget，每个 token 都在消耗它。所以组装上下文是每一轮都要做的策展，不是一次性写好的提示词。

## 违反它会怎样

- **框架自动拼的提示词你没读过。** 某框架的默认 Agent 提示词里有一句"如果不确定就询问用户"，你的语音产品于是每三句话就反问一次。你花了两周调自己那段提示词，问题在你没看过的那段里。
- **历史裁剪是框架默认的"保留最近 N 条"。** 用户在第 5 轮说的关键约束在第 25 轮被裁掉，模型开始违反它。没人知道为什么，因为没人看到过第 25 轮发给模型的完整窗口。
- **工具结果原样进上下文。** 一个返回 500 行的查询把窗口填满，之后每一轮都在为这 500 行付钱，模型还从里面"发现"了不存在的规律。
- **时间戳写在系统提示词第一行。** 每次请求前缀都不同，供应商的前缀缓存永远不命中。账单是本可以的两倍。

四个例子的共同点：问题出在"发给模型的东西"上，而这个东西没有人真正看过。

## 最小做法

一个函数负责组装，它的输出就是发给模型的东西，随时可以打印：

```python
def build_window(thread: Thread, retrieved: list[str], budget: int) -> list[Message]:
    fixed = [Message("system", SYSTEM_PROMPT)]              # stable prefix first
    if retrieved:
        fixed.append(Message("user", render_docs(retrieved)))
    spent = tokens(fixed)
    recent = []
    for m in reversed(thread.to_messages()):                  # newest first
        if spent + tokens(m) > budget:
            break
        recent.insert(0, m); spent += tokens(m)
    return fixed + recent                                     # print this when debugging

window = build_window(thread, docs, budget=8000)
log.debug("window", [m.content[:80] for m in window])       # you can always see it
reply = await model.complete(window, tools=specs)
```

`SYSTEM_PROMPT` 是一个常量，在仓库里，有 git 历史。`build_window` 是一个纯函数，可以单测。这两点做到，剩下的都是优化。

## 对照

- 参考：[12-factor-agents · factor 02 Own your prompts](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-02-own-your-prompts.md)、[factor 03 Own your context window](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-03-own-your-context-window.md)（访问日期 2026-09-04）；[Anthropic · Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)（访问日期 2026-09-04）
- 相关课程：[03 Prompt Engineering](../lessons/03-prompt-engineering/README.md)、[08 Agent 的 Context Engineering](../lessons/08-context-engineering-for-agents/README.md)

---

[← 原则总览](./README.md)
