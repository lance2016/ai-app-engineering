"""The same round trip against a real model. Default provider: DeepSeek.

Nothing in the loop changes compared to the fake adapter; only the adapter does.
If no key is configured the script explains how to set one and exits cleanly,
so the test suite stays green offline.

Run:  MODEL_PROVIDER=deepseek uv run python lessons/00-setup/code/02_real_model_tool_call.py
      MODEL_PROVIDER=dashscope uv run python lessons/00-setup/code/02_real_model_tool_call.py
Expect: the model asks for get_weather, the runtime answers it, the model replies in words.
"""

# %% imports
import asyncio
import json
import os

from aiapp import Message, ToolSpec, get_adapter

WEATHER_SPEC = ToolSpec(
    name="get_weather",
    description="Current weather for a city. Use it whenever the user asks about weather.",
    parameters={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)


# %% get_weather
def get_weather(city: str) -> str:
    return json.dumps({"city": city, "temp_c": 31, "condition": "sunny"})


# %% main
async def main() -> None:
    provider = os.environ.get("MODEL_PROVIDER", "fake")
    if provider == "fake":
        print("MODEL_PROVIDER is 'fake'. Set MODEL_PROVIDER=deepseek (and DEEPSEEK_API_KEY) to call a real model.")
        return
    model = get_adapter(provider)
    print(f"provider={model.name} model={getattr(model, 'model', '?')}")
    messages = [Message(role="user", content="What's the weather like in Shenzhen right now?")]
    for _ in range(4):
        reply = await model.complete(messages, tools=[WEATHER_SPEC])
        print(f"usage: in={reply.usage.input_tokens} out={reply.usage.output_tokens}")
        if not reply.wants_tool:
            print(f"assistant: {reply.content}")
            return
        messages.append(Message(role="assistant", content=reply.content, tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            print(f"model asked for {call.name}({call.arguments})")
            messages.append(Message(role="tool", tool_call_id=call.id, content=get_weather(call.arguments.get("city", ""))))
    print("step cap reached")


# %% run
if __name__ == "__main__":
    asyncio.run(main())
