# 00 环境与模型接入｜练习

## 练习 1：改剧本

把 `01_hello_fake_adapter.py` 里的 `get_adapter()` 换成 `FakeAdapter(script=[ModelResponse(content="I am a scripted model.")])`，再运行。

验收：第一行输出变成剧本里的句子；再多调一次 `complete`，第二次回到 echo。

<details><summary>提示</summary>

剧本用完之后 fake adapter 才会 echo。`from aiapp import FakeAdapter, ModelResponse`。

</details>

## 练习 2：读类型

不看代码回答：`ToolCall` 和 `Message(role="tool")` 分别代表工具调用过程中的哪个时刻？

<details><summary>答案</summary>

`ToolCall` 是模型的请求，出现在 assistant 消息里，此时什么都还没发生。`Message(role="tool")` 是运行时执行完之后回给模型的结果，用 `tool_call_id` 和请求对上。两者之间那一段，就是第 05 课要讲的全部内容。

</details>

## 练习 3：为什么不直接 mock

fake adapter 和在测试里 `mock.patch` 一个 SDK 调用有什么区别？各适合什么场景？

<details><summary>答案</summary>

fake adapter 实现的是课程自己定义的接口，和任何 SDK 无关，换供应商不用改测试。`mock.patch` 绑在某个 SDK 的函数签名上，SDK 升级或换家就失效。课程代码用前者；你在真实项目里给某个 SDK 写单测时用后者。

</details>
