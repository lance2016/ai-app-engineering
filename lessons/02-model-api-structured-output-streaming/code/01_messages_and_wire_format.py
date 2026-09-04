"""One model call, taken apart: the message list and what it becomes on the wire.

The course types (`Message`, `ToolCall`) are provider-neutral. The adapter
translates them into the provider's JSON. Print both and the translation
stops being magic: roles, tool results tied to call ids, and an error flag
that has to be encoded into the content because the wire format has none.

Run:  uv run python lessons/02-model-api-structured-output-streaming/code/01_messages_and_wire_format.py
Expect: four course messages and their OpenAI-compatible wire form side by side.
"""

# %% imports
import json

from aiapp import Message, ToolCall, ToolSpec
from aiapp.adapters.openai_compat import _to_wire, _tool_to_wire

# %% a_short_conversation
CALL = ToolCall(id="call_1", name="get_weather", arguments={"city": "Shenzhen"})
MESSAGES = [
    Message(role="system", content="You are terse."),
    Message(role="user", content="Weather in Shenzhen?"),
    Message(role="assistant", tool_calls=(CALL,)),
    Message(role="tool", tool_call_id="call_1", content="service unavailable", is_error=True),
]
SPEC = ToolSpec("get_weather", "Current weather for a city.", {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]})


# %% run
def main() -> None:
    for m in MESSAGES:
        print(f"course : {m}")
        print(f"wire   : {json.dumps(_to_wire(m), ensure_ascii=False)}\n")
    print("tool definition on the wire:")
    print(json.dumps(_tool_to_wire(SPEC), indent=2))
    print("\nnotice: the error flag became an 'ERROR:' prefix, and the tool result is linked to the call by id, not by position.")
    print("parameters like temperature and max_tokens travel next to `messages` in the same request body; see the README.")


if __name__ == "__main__":
    main()
