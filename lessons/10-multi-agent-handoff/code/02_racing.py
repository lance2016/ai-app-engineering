"""Racing: two models run in parallel on the same input; a rule decides whose output counts.

A chat model drafts a reply while a small classifier decides whether the user
issued a command. If the classifier says "command", the chat draft is cancelled
and the tool runs. If it says "chat", the draft is used. If the classifier is
late, the runtime falls back to the draft rather than making the user wait.

Run:  uv run python lessons/10-multi-agent-handoff/code/02_racing.py
      INJECT_CLASSIFIER_TIMEOUT=1 uv run python lessons/10-multi-agent-handoff/code/02_racing.py
Expect: the command path wins for "turn the light off"; with injection the
        classifier times out and the chat draft is used with a warning.
"""

# %% imports
import asyncio
import json
import os

from aiapp import FakeAdapter, Message, ModelResponse

INJECT_CLASSIFIER_TIMEOUT = os.environ.get("INJECT_CLASSIFIER_TIMEOUT") == "1"
CLASSIFIER_BUDGET = 0.2


# %% two_models
class DelayedFake(FakeAdapter):
    def __init__(self, delay: float, script):
        super().__init__(script)
        self.delay = delay

    async def complete(self, messages, tools=None):
        await asyncio.sleep(self.delay)
        return await super().complete(messages, tools)


# %% race
async def race(user_text: str, chat: FakeAdapter, classifier: FakeAdapter) -> str:
    history = [Message(role="user", content=user_text)]
    chat_task = asyncio.create_task(chat.complete(history))
    try:
        verdict = json.loads((await asyncio.wait_for(classifier.complete(history), CLASSIFIER_BUDGET)).content)
    except TimeoutError:
        print("  classifier late -> fall back to chat draft")
        return f"chat: {(await chat_task).content}"
    if verdict["intent"] == "command":
        chat_task.cancel()
        return f"command: execute {verdict['tool']}({verdict['args']})"
    if verdict["intent"] == "both":
        return f"command: execute {verdict['tool']}({verdict['args']}); chat: {(await chat_task).content}"
    return f"chat: {(await chat_task).content}"


# %% run
async def main() -> None:
    cases = [
        ("Turn the light off.", {"intent": "command", "tool": "set_light", "args": {"on": False}}),
        ("What's your favourite colour?", {"intent": "chat"}),
        ("Play some jazz and tell me about Miles Davis.", {"intent": "both", "tool": "play_music", "args": {"genre": "jazz"}}),
    ]
    for text, verdict in cases:
        chat = DelayedFake(0.05, [ModelResponse(content=f"(draft reply to: {text})")])
        classifier = DelayedFake(0.5 if INJECT_CLASSIFIER_TIMEOUT else 0.02, [ModelResponse(content=json.dumps(verdict))])
        print(f"user: {text}")
        print(f"  -> {await race(text, chat, classifier)}")


if __name__ == "__main__":
    asyncio.run(main())
