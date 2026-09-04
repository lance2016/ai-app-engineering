"""What a chat template does: turn roles into plain text with special tokens.

No training here, only string building. Every chat model was fine-tuned on
text shaped like this; the API renders it for you, a self-hosted model does
not. The final assistant marker tells the model it is its turn.

Run:  uv run python prerequisites/llm-foundations/05-training-and-alignment/code/01_chat_template.py
      INJECT_MISSING_TURN_MARKER=1 uv run python prerequisites/llm-foundations/05-training-and-alignment/code/01_chat_template.py
Expect: the rendered prompt. With the injection the trailing assistant marker
        is missing and the model would keep writing *as the user*.
"""

# %% imports
import os

INJECT_MISSING_TURN_MARKER = os.environ.get("INJECT_MISSING_TURN_MARKER") == "1"

# One common template shape. Real models use different tokens, same structure.
BOS, EOS = "<|begin|>", "<|end|>"


# %% render
def render(messages: list[dict[str, str]], *, add_generation_prompt: bool = True) -> str:
    parts = [BOS]
    for m in messages:
        parts.append(f"<|{m['role']}|>\n{m['content']}{EOS}\n")
    if add_generation_prompt:
        parts.append("<|assistant|>\n")  # "your turn"
    return "".join(parts)


# %% run
def main() -> None:
    messages = [
        {"role": "system", "content": "You are a terse assistant."},
        {"role": "user", "content": "What is 2+2?"},
    ]
    prompt = render(messages, add_generation_prompt=not INJECT_MISSING_TURN_MARKER)
    print(prompt)
    print("---")
    print(f"the model sees {len(prompt)} characters of plain text; roles are just segments fenced by special tokens.")
    if INJECT_MISSING_TURN_MARKER:
        print("no trailing <|assistant|> marker: from the model's point of view the user has not finished speaking,")
        print("so it will continue the user's turn instead of answering. This is the classic self-hosting bug.")


if __name__ == "__main__":
    main()
