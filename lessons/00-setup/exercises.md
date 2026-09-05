# 00 起步｜练习

## 练习 1：把最小例子改成流式

正文的最小例子是一次性拿到完整回答。给 `client.chat.completions.create` 加上 `stream=True`，边收边打印。

<details><summary>提示与讨论</summary>

```python
stream = client.chat.completions.create(
    model="deepseek-chat", messages=messages, stream=True
)
for chunk in stream:
    delta = chunk.choices[0].delta.content
    if delta:
        print(delta, end="", flush=True)
```

跑一次你会立刻发现一个问题：流式模式下，工具调用的参数是**一片一片**来的，`delta.tool_calls[0].function.arguments` 每次只有几个字符，要自己按 `index` 拼起来才能 `json.loads`。

这就是第 02 课要处理的事情，也是为什么适配器这层抽象值得有——拼接逻辑写一次，所有调用方都不用管。

</details>

## 练习 2：读类型

不看代码回答：模型返回的「工具调用请求」和你回给模型的「工具结果」，分别代表工具调用过程中的哪个时刻？它们靠什么对上？

<details><summary>答案</summary>

工具调用请求出现在 assistant 消息里，此时**什么都还没发生**——模型只是表达了意图。工具结果是 `role="tool"` 的消息，是运行时真的执行完之后回给模型的，靠 `tool_call_id` 和请求配对。

这两者之间那一段，就是第 05 课要讲的全部内容：参数可能非法、工具可能失败、副作用可能重复执行。模型说要做，不等于做成了。

</details>

## 练习 3：为什么不直接 mock

用一个自己定义的 fake adapter，和在测试里 `mock.patch` 一个 SDK 调用，有什么区别？各适合什么场景？

<details><summary>答案</summary>

fake adapter 实现的是你自己定义的接口，和任何 SDK 无关。换供应商不用改测试，因为测试从来没见过供应商。

`mock.patch` 绑在某个 SDK 的函数签名上。SDK 升级改了参数名，或者你换一家供应商，测试就得跟着改——而且它是「假绿」：测试通过了，真实调用可能早就坏了。

讲机制、写业务测试用前者；专门给「我们的适配器是否正确调用了这个 SDK」写一个薄薄的单测时，用后者。

</details>

## 练习 4：判断一段代码属于哪一层

下面这行出现在一个业务模块里，问题在哪？

```python
resp = openai_client.chat.completions.create(model="gpt-4o", messages=msgs)
```

<details><summary>答案</summary>

三个问题，从轻到重：

1. **模型名硬编码**。换模型要改业务代码，A/B 测两个模型做不到。
2. **供应商 SDK 出现在业务层**。这一行等于宣布：整个模块和 OpenAI 绑死了。
3. **没有超时、没有重试、没有用量记账**。这三件事每个调用点都要做一遍，除非收进适配器。

正确的形态是业务层只看到 `await model.complete(messages, tools=...)`，上面三件事在适配器里做一次。这就是第 12 条原则。

</details>
