"""Fact #2 of a successful tool call: the arguments are valid.

The model returns arguments; the runtime validates them against the tool's
schema before anything runs. Invalid arguments are fed back to the model as
an error result so it can correct itself. The runtime never guesses.

Run:  uv run python lessons/05-tool-calling/code/01_schema_validation.py
      INJECT_BAD_ARGS=1 uv run python lessons/05-tool-calling/code/01_schema_validation.py
Expect: without injection, one tool call and a final answer.
        With injection, a validation error goes back to the model, then a corrected call.
"""

# %% imports
import asyncio
import json
import os
from typing import Literal

from pydantic import BaseModel, ValidationError

from aiapp import FakeAdapter, Message, ModelResponse, ToolCall, ToolSpec, tool_call_response

INJECT_BAD_ARGS = os.environ.get("INJECT_BAD_ARGS") == "1"


# %% GetWeatherArgs
class GetWeatherArgs(BaseModel):
    city: str
    unit: Literal["celsius", "fahrenheit"] = "celsius"


WEATHER_SPEC = ToolSpec(
    name="get_weather",
    description="Current weather for a city.",
    parameters=GetWeatherArgs.model_json_schema(),
)


# %% get_weather
def get_weather(args: GetWeatherArgs) -> str:
    return json.dumps({"city": args.city, "temp": 31, "unit": args.unit})


# %% run_tool
def run_tool(call: ToolCall) -> Message:
    """Validate first. A schema error is a *result*, not an exception."""
    try:
        args = GetWeatherArgs.model_validate(call.arguments)
    except ValidationError as exc:
        return Message(role="tool", tool_call_id=call.id, is_error=True, content=f"invalid arguments: {exc.errors()[0]['msg']}")
    return Message(role="tool", tool_call_id=call.id, content=get_weather(args))


# %% build_script
def build_script() -> list[ModelResponse]:
    good = tool_call_response("get_weather", {"city": "Shenzhen", "unit": "celsius"})
    final = ModelResponse(content="It is 31°C in Shenzhen.")
    if not INJECT_BAD_ARGS:
        return [good, final]
    bad = tool_call_response("get_weather", {"city": "Shenzhen", "unit": "kelvin"})
    return [bad, good, final]


# %% main
async def main() -> None:
    model = FakeAdapter(script=build_script())
    messages = [Message(role="user", content="What's the weather in Shenzhen?")]
    for _ in range(5):  # hard step cap; lesson 06 makes this a real budget
        reply = await model.complete(messages, tools=[WEATHER_SPEC])
        if not reply.wants_tool:
            print(f"assistant: {reply.content}")
            return
        messages.append(Message(role="assistant", tool_calls=reply.tool_calls))
        for call in reply.tool_calls:
            result = run_tool(call)
            tag = "ERROR" if result.is_error else "ok"
            print(f"tool {call.name}({call.arguments}) -> [{tag}] {result.content}")
            messages.append(result)
    print("step cap reached")


# %% run
if __name__ == "__main__":
    asyncio.run(main())
