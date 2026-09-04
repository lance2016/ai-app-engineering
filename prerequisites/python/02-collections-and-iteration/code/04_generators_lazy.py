"""Generators produce values one at a time instead of building a whole list.

Run:  uv run python prerequisites/python/02-collections-and-iteration/code/04_generators_lazy.py
Expect: a generator object, then values pulled one by one, then a sum over a
        stream that would be too big to hold in a list.
"""


# %% generator_function
def countdown(n: int):
    while n > 0:
        yield n  # pause here, hand out n, resume on the next request
        n -= 1


gen = countdown(3)
print("generator object:", gen)
print(next(gen), next(gen), next(gen))

# %% generator_expression
squares = (i * i for i in range(5))
print("squares:", list(squares))

# %% lazy_saves_memory
total = sum(i for i in range(10_000_000))  # never builds a 10-million-item list
print("sum:", total)

# %% enumerate_zip_sorted
names = ["Zed", "amy", "Bob"]
for index, name in enumerate(names, start=1):
    print(index, name)
print(list(zip(names, [3, 1, 2])))
print(sorted(names, key=str.lower))
