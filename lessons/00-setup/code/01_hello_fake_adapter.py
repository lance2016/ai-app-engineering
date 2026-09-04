"""First contact with the shared runtime.

Run:  uv run python lessons/00-setup/code/01_hello_fake_adapter.py
Expect: two lines, one echo from the fake model and one token count.
"""

# %% imports
import asyncio
import os

from aiapp import Message, get_adapter


# %% main
async def main() -> None:
    if os.environ.get("INJECT_MISSING_PROVIDER"):
        print("injected failure: provider configuration is missing; fix MODEL_PROVIDER before starting")
        return
    model = get_adapter()  # MODEL_PROVIDER defaults to "fake"
    reply = await model.complete([Message(role="user", content="hello, who are you?")])
    print(f"provider={model.name} reply={reply.content!r}")
    print(f"usage: in={reply.usage.input_tokens} out={reply.usage.output_tokens}")


# %% run
if __name__ == "__main__":
    asyncio.run(main())
