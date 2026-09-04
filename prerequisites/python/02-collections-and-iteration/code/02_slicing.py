"""Slicing: take a piece of a list or string without a loop.

Run:  uv run python prerequisites/python/02-collections-and-iteration/code/02_slicing.py
Expect: several slices of the same list and one of a string.
"""

# %% basics
messages = ["m0", "m1", "m2", "m3", "m4", "m5"]
print("first three:", messages[:3])
print("last two:", messages[-2:])
print("middle:", messages[2:4])
print("every other:", messages[::2])
print("reversed:", messages[::-1])

# %% strings_slice_too
text = "Hello, world"
print(text[:5], "|", text[-5:])

# %% keep_recent_history
history = list(range(20))
recent = history[-5:]  # a common pattern: keep only the newest N items
print("recent:", recent)
