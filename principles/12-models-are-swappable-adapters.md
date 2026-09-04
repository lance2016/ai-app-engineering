---
status: complete
---

# 原则 12｜模型是可替换的适配器，任何代码都不该绑死一家供应商

> 今天最合适的模型，六个月后未必是。价格会变，能力会变，可访问性会变。把供应商的 SDK 调用包在一个你自己定义的接口后面，换模型就是换一个环境变量。

## 主张

应用代码只和一个自己定义的协议说话：给它一串消息和可选的工具，它返回一个响应或一条增量流。供应商的 SDK、请求体格式、返回结构、错误类型，全部封在 adapter 里。协议是你的，adapter 是供应商的。

这不是为了"将来可能换"的抽象，而是有几个眼前的收益：

1. **离线可跑。** 同一个协议可以有一个按剧本回答的 fake 实现，测试和课程代码不需要 API key，行为确定，可以断言。
2. **可访问性不锁死架构。** 本课程默认真实模型用 DeepSeek，只因为它在国内可直接访问；DashScope、OpenAI 都走 OpenAI 兼容协议，同一个 adapter 换 base URL 和 key 就行。有一天需要 Anthropic 的原生特性，加一个 adapter，业务代码不动。
3. **评测能横向比。** 同一份 golden set，换 `MODEL_PROVIDER` 跑一遍就是另一个模型的成绩。绑死一家时，"换模型会不会更好"这个问题根本问不出来。
4. **翻译损耗看得见。** 课程类型里有 `is_error`，线上格式没有，adapter 把它翻译成内容前缀。这种损耗集中在一个文件里，而不是散在业务代码的每个调用点。

## 违反它会怎样

- **业务代码到处 `import openai`。** 换供应商时要改几十个文件，每个调用点的参数名、返回字段、异常类型都不一样。团队评估后决定"算了，先不换"，于是被价格和限流牵着走。
- **测试依赖真实 API。** CI 要 key，跑一次要钱，网络抖动导致随机失败，最后大家把测试标成 skip。没有 fake 实现，就没有确定性的测试。
- **供应商特有字段泄漏到业务层。** 某处代码读 `response.choices[0].message.tool_calls[0].function.arguments` 再 `json.loads`，换到另一家时字段名和类型都变了，而且这行代码复制在了五个地方。
- **绑死之后被单点故障拖垮。** 供应商限流或宕机，没有第二条路。第 19 课的 Fallback 路由前提就是有两个能互换的 adapter。

## 最小做法

协议只有两个方法；工厂函数按环境变量选实现；预设表让"加一家兼容供应商"只需三行：

```python
class ModelAdapter(Protocol):
    name: str
    async def complete(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> ModelResponse: ...
    def stream(self, messages: list[Message], tools: list[ToolSpec] | None = None) -> AsyncIterator[StreamChunk]: ...

PRESETS = {
    "deepseek":  ProviderPreset("https://api.deepseek.com", "DEEPSEEK_API_KEY", "deepseek-chat"),
    "dashscope": ProviderPreset("https://dashscope.aliyuncs.com/compatible-mode/v1", "DASHSCOPE_API_KEY", "qwen-plus"),
    "openai":    ProviderPreset("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
}

def get_adapter(provider: str | None = None) -> ModelAdapter:
    provider = (provider or os.environ.get("MODEL_PROVIDER") or "fake").lower()
    if provider == "fake":
        return FakeAdapter()
    preset = PRESETS[provider]
    return OpenAICompatibleAdapter(name=provider, api_key=os.environ[preset.key_env],
                                   base_url=preset.base_url, model=preset.default_model)
```

业务代码只写 `model = get_adapter()`，然后 `await model.complete(...)`。它不知道也不需要知道后面是谁。

## 对照

- 参考：本仓库 [`project/src/aiapp/adapters/`](../project/src/aiapp/adapters/) 是这条原则的完整实现；DeepSeek、DashScope 的 OpenAI 兼容接口见 [DeepSeek API 文档](https://api-docs.deepseek.com/) 与 [阿里云 DashScope 兼容模式](https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope)（访问日期 2026-09-04）。12-factor-agents 没有直接对应的 factor，但 factor 02 和 factor 03 的"自己掌控 prompt 和上下文"与此同源：你能掌控的前提是中间没有黑盒。
- 相关课程：[00 环境与模型接入](../lessons/00-setup/README.md)、[02 模型调用、结构化输出与流式](../lessons/02-model-api-structured-output-streaming/README.md)、[19 可靠性、成本、部署与 LLMOps](../lessons/19-reliability-cost-llmops/README.md)、[21 模型适配、微调与推理服务](../lessons/21-model-adaptation-finetuning-inference/README.md)

---

[← 原则总览](./README.md)
