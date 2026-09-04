"""Comprehensions: build a new container from an old one in one line.

Run:  uv run python prerequisites/python/02-collections-and-iteration/code/03_comprehensions.py
Expect: the same result computed with a loop and with a comprehension, then
        dict and set comprehensions.
"""

# %% loop_version
words = ["apple", "kiwi", "banana", "fig"]
lengths_loop = []
for word in words:
    lengths_loop.append(len(word))
print("loop:", lengths_loop)

# %% list_comprehension
lengths = [len(word) for word in words]
print("comprehension:", lengths)

# %% with_condition
long_words = [word.upper() for word in words if len(word) > 4]
print("long words:", long_words)

# %% dict_and_set
word_to_len = {word: len(word) for word in words}
first_letters = {word[0] for word in words}
print("dict:", word_to_len)
print("set:", first_letters)
