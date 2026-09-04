"""Strings: the type you will use most, and f-strings to build them.

Run:  uv run python prerequisites/python/01-python-basics/code/02_strings_and_fstrings.py
Expect: a formatted sentence, a few string methods, and a multi-line string.
"""

# %% fstring
city = "Shenzhen"
temp = 31.456
print(f"It is {temp:.1f} degrees in {city}.")  # :.1f keeps one decimal

# %% methods
reply = "  Sure, I can help!  "
print(reply.strip())
print(reply.strip().lower())
print(reply.strip().startswith("Sure"))
print(reply.strip().split(" "))

# %% multiline
prompt = """You are a helpful assistant.
Answer in one sentence."""
print(prompt)
print("Lines:", len(prompt.splitlines()))
